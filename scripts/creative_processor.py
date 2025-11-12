#!/usr/bin/env python3
"""
Creative Asset Management System
Processes video and image files with dual naming pattern support.
"""

import os
import sys
import json
import secrets
import re
from pathlib import Path
from datetime import datetime
import subprocess
from math import gcd

try:
    import pandas as pd
    from PIL import Image
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


class CreativeProcessor:
    """Main processor for creative assets"""
    
    def __init__(self, base_path, dry_run=False, interactive=True, force_reprocess=False, native=False):
        self.base_path = Path(base_path)
        self.source_dir = self.base_path / "source_files"
        self.upload_dir = self.base_path / "uploaded"
        self.tracking_dir = self.base_path / "tracking"
        self.dry_run = dry_run
        self.interactive = interactive
        self.force_reprocess = force_reprocess
        
        # File type mappings (must be defined before _detect_native_folder)
        self.video_extensions = {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.flv', '.wmv'}
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        
        # Native processing modes:
        # - force_native: --native flag forces ALL videos to native format
        # - native_mode: native folder exists (only process files IN that folder)
        self.force_native = native
        self.native_mode = self._detect_native_folder()
        
        # File paths
        self.ids_file = self.tracking_dir / "processed_ids.json"
        self.defaults_file = self.tracking_dir / "metadata_defaults.csv"
        self.output_csv = self.tracking_dir / "creative_inventory.csv"  # Master inventory (cumulative)
        self.session_csv = self.tracking_dir / "creative_inventory_session.csv"  # Current session only
        
        # Data storage
        self.processed_ids = self._load_processed_ids()
        self.metadata_defaults = self._load_metadata_defaults()
        self.existing_files = self._load_existing_inventory()
        self.inventory_data = []
        self.new_folders_added = {}  # Track folders added during this session
        self.skipped_count = 0  # Track already-processed files
        
        # Native output directories (create if either force_native or native_mode)
        if self.force_native or self.native_mode:
            self.native_video_dir = self.upload_dir / "Native" / "Video"
            self.native_image_dir = self.upload_dir / "Native" / "Image"
            self.native_video_dir.mkdir(parents=True, exist_ok=True)
            self.native_image_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_processed_ids(self):
        """Load list of already processed unique IDs"""
        if self.ids_file.exists():
            with open(self.ids_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _detect_native_folder(self):
        """Check if source_files/native/ folder exists"""
        native_folder = self.source_dir / "native"
        return native_folder.exists() and native_folder.is_dir()
    
    def _is_native_file(self, file_path):
        """Check if a specific file is inside the source_files/native/ folder"""
        try:
            native_folder = self.source_dir / "native"
            # Check if file_path is relative to native_folder
            file_path.relative_to(native_folder)
            return True
        except ValueError:
            # File is not inside native folder
            return False
    
    def _save_processed_id(self, unique_id):
        """Save a new unique ID to prevent duplicates"""
        self.processed_ids.add(unique_id)
        if not self.dry_run:
            with open(self.ids_file, 'w') as f:
                json.dump(list(self.processed_ids), f, indent=2)
    
    def _load_metadata_defaults(self):
        """Load metadata defaults for folder-based processing"""
        if self.defaults_file.exists():
            df = pd.read_csv(self.defaults_file)
            
            # Check for duplicate folder names
            duplicates = df[df.duplicated('folder_path', keep=False)]
            if not duplicates.empty:
                dup_folders = duplicates['folder_path'].unique()
                print(f"\n{'='*80}")
                print(f"❌ ERROR: Duplicate folder names in {self.defaults_file.name}")
                print(f"{'='*80}")
                print(f"The following folders appear multiple times:")
                for folder in dup_folders:
                    print(f"  - {folder}")
                print(f"\nPlease edit {self.defaults_file} and remove the duplicates.")
                print(f"Each folder should only appear once!")
                print(f"{'='*80}\n")
                sys.exit(1)
            
            return df.set_index('folder_path').to_dict('index')
        return {}
    
    def _load_existing_inventory(self):
        """Load existing processed files from CSV to detect duplicates"""
        if self.output_csv.exists():
            try:
                df = pd.read_csv(self.output_csv)
                # Track by source_path to handle same filename in different folders
                if 'source_path' in df.columns:
                    return set(df['source_path'].tolist())
            except Exception as e:
                print(f"Warning: Could not load existing inventory: {e}")
        return set()
    
    def _save_metadata_defaults(self):
        """Save updated metadata defaults to CSV"""
        if not self.new_folders_added:
            return
        
        # Load existing data
        if self.defaults_file.exists():
            df = pd.read_csv(self.defaults_file)
        else:
            df = pd.DataFrame(columns=['folder_path', 'category_name', 'creator_name', 'language', 'content_type', 'creative_description'])
        
        # Add new folders
        new_rows = []
        for folder, defaults in self.new_folders_added.items():
            new_rows.append({
                'folder_path': folder,
                'category_name': defaults.get('category_name', folder),  # Default to folder name if not specified
                'creator_name': defaults['creator_name'],
                'language': defaults['language'],
                'content_type': defaults['content_type'],
                'creative_description': defaults.get('creative_description', 'Generic')
            })
        
        # Append and save
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        df.to_csv(self.defaults_file, index=False)
        print(f"\n✓ Saved {len(new_rows)} new folder(s) to {self.defaults_file.name}")
    
    def _prompt_for_folder_defaults(self, folder_name):
        """Interactively prompt user for folder defaults"""
        print(f"\n{'='*80}")
        print(f"⚠️  NEW FOLDER DETECTED: '{folder_name}'")
        print(f"{'='*80}")
        print("This folder is not in metadata_defaults.csv.")
        
        # Show existing folders
        if self.metadata_defaults:
            print("\n📁 EXISTING FOLDERS in metadata_defaults.csv:")
            existing_folders = sorted(self.metadata_defaults.keys())
            for i, folder in enumerate(existing_folders, 1):
                defaults = self.metadata_defaults[folder]
                print(f"  {i}. {folder} ({defaults.get('creator_name', 'N/A')}, {defaults.get('language', 'N/A')}, {defaults.get('content_type', 'N/A')})")
            
            print(f"\n❓ Is '{folder_name}' the same as one of these folders?")
            print("   (Maybe just named differently?)")
            
            # Ask if they want to use an existing folder
            while True:
                choice = input(f"\nEnter number (1-{len(existing_folders)}) to use that folder, or 'N' to create new: ").strip().upper()
                
                if choice == 'N':
                    break
                
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(existing_folders):
                        # Use existing folder's defaults
                        selected_folder = existing_folders[choice_num - 1]
                        defaults = self.metadata_defaults[selected_folder].copy()
                        
                        # Get the canonical category name from the selected folder
                        category_name = defaults.get('category_name', selected_folder)
                        
                        print(f"\n✓ Using defaults from '{selected_folder}'")
                        print(f"  Category: {category_name}")
                        print(f"  Creator: {defaults.get('creator_name')}, Language: {defaults.get('language')}, Type: {defaults.get('content_type')}, Description: {defaults.get('creative_description')}")
                        print(f"\n💡 TIP: Consider renaming your folder from '{folder_name}' to '{selected_folder}' to avoid this prompt next time!")
                        
                        # Create new defaults with the selected category
                        new_defaults = defaults.copy()
                        new_defaults['category_name'] = category_name
                        
                        # Save to session cache with the NEW folder name
                        self.new_folders_added[folder_name] = new_defaults
                        self.metadata_defaults[folder_name] = new_defaults
                        
                        return new_defaults
                except ValueError:
                    pass
                
                print(f"Please enter a number between 1 and {len(existing_folders)}, or 'N' for new")
        
        # Create new folder entry
        print("\n📝 Creating NEW folder entry...")
        print("Please provide default values for files in this folder:\n")
        
        # Get creator name
        creator_name = input("Creator Name (e.g., Seras, Pedro, Maria): ").strip()
        if not creator_name:
            creator_name = "Unknown"
        
        # Get language
        language = input("Language Code (e.g., EN, ES, FR, JP): ").strip().upper()
        if not language:
            language = "EN"
        
        # Get content type
        while True:
            content_type = input("Content Type (SFW or NSFW): ").strip().upper()
            if content_type in ['SFW', 'NSFW']:
                break
            print("Please enter either 'SFW' or 'NSFW'")
        
        # Get creative description
        creative_desc = input("Creative Description (default: Generic): ").strip()
        if not creative_desc:
            creative_desc = "Generic"
        
        defaults = {
            'category_name': folder_name,  # By default, category name = folder name
            'creator_name': creator_name,
            'language': language,
            'content_type': content_type,
            'creative_description': creative_desc
        }
        
        print(f"\n✓ Created new defaults for '{folder_name}' folder")
        print(f"  Category: {folder_name}")
        print(f"  Creator: {creator_name}, Language: {language}, Type: {content_type}, Description: {creative_desc}")
        
        # Save to session cache and metadata_defaults dict
        self.new_folders_added[folder_name] = defaults
        self.metadata_defaults[folder_name] = defaults
        
        return defaults
    
    def _cleanup_empty_folders(self):
        """Remove empty folders from source_files directory"""
        removed_folders = []
        
        # Walk through source_files directory (bottom-up to handle nested folders)
        for root, dirs, files in os.walk(self.source_dir, topdown=False):
            # Skip the source_files root itself
            if Path(root) == self.source_dir:
                continue
            
            # Check if folder is empty
            if not os.listdir(root):
                try:
                    os.rmdir(root)
                    folder_name = Path(root).relative_to(self.source_dir)
                    removed_folders.append(str(folder_name))
                except Exception as e:
                    print(f"Warning: Could not remove empty folder {root}: {e}")
        
        if removed_folders:
            print(f"\n🗑️  Cleaned up {len(removed_folders)} empty folder(s) from source_files/:")
            for folder in removed_folders:
                print(f"    - {folder}")
    
    def generate_unique_id(self):
        """Generate a unique ID in format: ID-XXXXXXXX"""
        while True:
            random_hex = secrets.token_hex(4).upper()
            unique_id = f"ID-{random_hex}"
            if unique_id not in self.processed_ids:
                return unique_id
    
    def get_video_metadata(self, file_path):
        """Extract metadata from video files using ffprobe"""
        try:
            # Get video duration
            duration_cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(file_path)
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip()) if duration_result.stdout.strip() else 0
            
            # Get video dimensions
            width_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(file_path)
            ]
            width_result = subprocess.run(width_cmd, capture_output=True, text=True)
            width = int(width_result.stdout.strip()) if width_result.stdout.strip() else 0
            
            height_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=height', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(file_path)
            ]
            height_result = subprocess.run(height_cmd, capture_output=True, text=True)
            height = int(height_result.stdout.strip()) if height_result.stdout.strip() else 0
            
            # Calculate aspect ratio
            if width and height:
                # Simplify aspect ratio using GCD
                divisor = gcd(width, height)
                simplified_width = width // divisor
                simplified_height = height // divisor
                aspect_ratio = f"{simplified_width}:{simplified_height}"
                aspect_decimal = round(width / height, 4)
            else:
                aspect_ratio = "Unknown"
                aspect_decimal = 0
            
            return {
                'duration_seconds': round(duration, 2),
                'width_px': width,
                'height_px': height,
                'aspect_ratio': aspect_ratio,
                'aspect_decimal': aspect_decimal
            }
        except Exception as e:
            print(f"WARNING: Could not extract video metadata from {file_path}: {e}")
            return {
                'duration_seconds': 0,
                'width_px': 0,
                'height_px': 0,
                'aspect_ratio': 'Unknown',
                'aspect_decimal': 0
            }
    
    def get_image_metadata(self, file_path):
        """Extract metadata from image files using Pillow"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                # Simplify aspect ratio using GCD
                divisor = gcd(width, height)
                simplified_width = width // divisor
                simplified_height = height // divisor
                aspect_ratio = f"{simplified_width}:{simplified_height}"
                aspect_decimal = round(width / height, 4)
                
                return {
                    'duration_seconds': 0,
                    'width_px': width,
                    'height_px': height,
                    'aspect_ratio': aspect_ratio,
                    'aspect_decimal': aspect_decimal
                }
        except Exception as e:
            print(f"WARNING: Could not extract image metadata from {file_path}: {e}")
            return {
                'duration_seconds': 0,
                'width_px': 0,
                'height_px': 0,
                'aspect_ratio': 'Unknown',
                'aspect_decimal': 0
            }
    
    def parse_structured_filename(self, filename):
        """
        Parse Pattern 1: (Language)_(Category)_(Type)_(Creative-Name)_(Your-Name).ext
        Returns dict with extracted data or None if doesn't match
        """
        # Remove extension
        name_without_ext = Path(filename).stem
        
        # Split by underscore
        parts = name_without_ext.split('_')
        
        # Need at least 5 parts for structured pattern
        if len(parts) >= 5:
            return {
                'language': parts[0],
                'category': parts[1],
                'content_type': parts[2],
                'creative_name': parts[3],
                'creator_name': parts[4]
            }
        return None
    
    def parse_simple_filename(self, filename):
        """
        Parse Pattern 2: video-XXXXXXXX.ext or image-XXXXXXXX.ext
        Returns True if matches simple pattern
        """
        pattern = r'^(video|image)-[a-f0-9]{8}\.(mp4|mov|avi|jpg|jpeg|png|gif|webm)$'
        return bool(re.match(pattern, filename.lower()))
    
    def get_folder_category(self, file_path):
        """Extract category from parent folder name"""
        parent_folder = file_path.parent.name
        # If in source_files root, no category
        if parent_folder == "source_files":
            return None
        return parent_folder
    
    def resolve_metadata(self, file_path, parsed_data):
        """
        Resolve metadata using priority order:
        1. Parsed filename data
        2. Metadata defaults (folder match)
        3. Interactive prompt (if enabled)
        4. Folder name for category
        5. Flag for manual entry
        """
        metadata = {
            'language': None,
            'category': None,
            'content_type': None,
            'creative_name': None,
            'creator_name': None
        }
        
        # If we have parsed data from structured filename, use it
        if parsed_data:
            metadata.update(parsed_data)
            return metadata, "Pattern 1 (Structured)"
        
        # Otherwise, try to get from folder defaults
        folder_category = self.get_folder_category(file_path)
        
        if folder_category:
            # Look for defaults for this folder
            if folder_category in self.metadata_defaults:
                defaults = self.metadata_defaults[folder_category]
                # Use category_name from CSV if available, otherwise use folder name
                metadata['category'] = defaults.get('category_name', folder_category)
                metadata['creator_name'] = defaults.get('creator_name')
                metadata['language'] = defaults.get('language')
                metadata['content_type'] = defaults.get('content_type')
                metadata['creative_name'] = defaults.get('creative_description', 'Generic')
                return metadata, "Pattern 2 (Simple), defaults applied"
            
            # If interactive mode and folder not in defaults, prompt user
            if self.interactive and not self.dry_run:
                defaults = self._prompt_for_folder_defaults(folder_category)
                metadata['category'] = defaults.get('category_name', folder_category)
                metadata['creator_name'] = defaults.get('creator_name')
                metadata['language'] = defaults.get('language')
                metadata['content_type'] = defaults.get('content_type')
                metadata['creative_name'] = defaults.get('creative_description', 'Generic')
                return metadata, "Pattern 2 (Simple), interactive defaults added"
            
            # No match in CSV and not interactive, use folder name as category
            metadata['category'] = folder_category
        
        # If we still don't have data, flag for manual entry
        return metadata, "NEEDS MANUAL REVIEW"
    
    def classify_creative_type(self, file_path, metadata_info):
        """
        Classify as: video, image, or short_video
        Short video: duration < 23 seconds AND aspect ratio = 9:16
        """
        ext = file_path.suffix.lower()
        
        if ext in self.image_extensions:
            return 'image'
        
        if ext in self.video_extensions:
            duration = metadata_info.get('duration_seconds', 0)
            aspect_decimal = metadata_info.get('aspect_decimal', 0)
            
            # Check for 9:16 aspect ratio (0.5625)
            is_916 = abs(aspect_decimal - 0.5625) < 0.01  # Allow small tolerance
            
            if duration < 23 and is_916:
                return 'short_video'
            return 'video'
        
        return 'unknown'
    
    def generate_new_filename(self, unique_id, metadata, file_ext, duration_seconds=None, is_native_original=False):
        """
        Generate new filename: Lang_Category_Type_Name_Creator_Duration_ID.ext
        For videos: EN_Ahegao_NSFW_Generic_Seras_5sec_ID-F40623FA.mp4
        For native originals: ORG_EN_Ahegao_NSFW_Generic_Seras_5sec_ID-F40623FA.mp4
        For images: EN_Ahegao_NSFW_Generic_Seras_ID-F40623FA.jpg
        """
        parts = [
            metadata.get('language', 'UNK'),
            metadata.get('category', 'UNK'),
            metadata.get('content_type', 'UNK'),
            metadata.get('creative_name', 'Generic'),
            metadata.get('creator_name', 'UNK')
        ]
        
        # Add duration for videos (rounded to nearest second)
        if duration_seconds is not None and duration_seconds > 0:
            duration_sec = int(round(duration_seconds))
            parts.append(f"{duration_sec}sec")
        
        # Add unique ID at the end
        parts.append(unique_id)
        
        # Sanitize each part
        sanitized_parts = []
        for part in parts:
            if part is None:
                part = 'UNK'
            # Remove special characters, keep alphanumeric and hyphens
            sanitized = re.sub(r'[^a-zA-Z0-9-]', '', str(part))
            sanitized_parts.append(sanitized)
        
        # Add ORG_ prefix if this is an original that will be converted to native
        if is_native_original:
            new_filename = 'ORG_' + '_'.join(sanitized_parts) + file_ext
        else:
            new_filename = '_'.join(sanitized_parts) + file_ext
        
        return new_filename
    
    def _generate_native_filename(self, unique_id, metadata, prefix, duration_seconds=None):
        """
        Generate filename with VID_/IMG_ prefix and -VID/-IMG suffix.
        For videos: VID_EN_Ahegao_NSFW_Generic_Seras_4sec_ID-F40623FA-VID.mp4
        For images: IMG_EN_Ahegao_NSFW_Generic_Seras_ID-F40623FA-IMG.png
        
        Args:
            unique_id: Base unique ID (e.g., "ID-F40623FA")
            metadata: Metadata dict with language, category, etc.
            prefix: 'VID' or 'IMG'
            duration_seconds: Include for videos, None for images
        
        Returns:
            Formatted filename string
        """
        parts = [
            prefix,
            metadata.get('language', 'UNK'),
            metadata.get('category', 'UNK'),
            metadata.get('content_type', 'UNK'),
            metadata.get('creative_name', 'Generic'),
            metadata.get('creator_name', 'UNK')
        ]
        
        # Add duration for videos (rounded to nearest second)
        if duration_seconds is not None and duration_seconds > 0:
            duration_sec = int(round(duration_seconds))
            parts.append(f"{duration_sec}sec")
        
        # Add unique ID with suffix at the end
        parts.append(f"{unique_id}-{prefix}")
        
        # Sanitize each part
        sanitized_parts = []
        for part in parts:
            if part is None:
                part = 'UNK'
            # Remove special characters, keep alphanumeric and hyphens
            sanitized = re.sub(r'[^a-zA-Z0-9-]', '', str(part))
            sanitized_parts.append(sanitized)
        
        # Set extension based on prefix
        ext = '.mp4' if prefix == 'VID' else '.png'
        
        return '_'.join(sanitized_parts) + ext
    
    def _process_native_pair(self, file_path, base_id, metadata, original_tech_metadata):
        """
        Process video for native format, creating video + image pair.
        
        Args:
            file_path: Path to original video file
            base_id: Base unique ID (e.g., "ID-F40623FA")
            metadata: Metadata dict with language, category, etc.
            original_tech_metadata: Original video technical metadata
        
        Returns:
            List of 2 records (video and image) for CSV
        """
        try:
            from native_converter import NativeConverter
            
            converter = NativeConverter()
            
            # Get file size
            file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
            
            # Generate filenames with VID_/IMG_ prefixes and -VID/-IMG suffixes
            # Native videos are max 4 seconds, so use 4 as placeholder for filename
            video_filename = self._generate_native_filename(
                base_id, metadata, 'VID', 4.0
            )
            image_filename = self._generate_native_filename(
                base_id, metadata, 'IMG', None
            )
            
            video_path = self.native_video_dir / video_filename
            image_path = self.native_image_dir / image_filename
            
            print(f"  Converting to native format:")
            print(f"    Video: {video_filename}")
            print(f"    Image: {image_filename}")
            
            # Convert using native_converter
            if not self.dry_run:
                result = converter.convert_video(file_path, video_path, image_path)
                
                if not result['success']:
                    print(f"  ✗ Native conversion failed: {result.get('error', 'Unknown error')}")
                    return []
                
                actual_duration = result.get('duration', 4.0)
                print(f"  ✓ Native conversion successful ({actual_duration}s)")
            else:
                print(f"  [DRY RUN] Would convert to native format")
                actual_duration = 4.0  # Placeholder for dry run
            
            # Create inventory records for both
            video_record = {
                'unique_id': f"{base_id}-VID",
                'original_filename': file_path.name,
                'new_filename': video_filename,
                'creator_name': metadata.get('creator_name', ''),
                'language': metadata.get('language', ''),
                'category': metadata.get('category', ''),
                'content_type': metadata.get('content_type', ''),
                'creative_type': 'native_video',
                'duration_seconds': actual_duration if not self.dry_run else 4.0,
                'aspect_ratio': '16:9',  # Native videos are 640x360 = 16:9
                'width_px': 640,
                'height_px': 360,
                'file_size_mb': file_size_mb if not self.dry_run else round(file_size_mb * 0.3, 2),  # Estimate
                'file_format': 'mp4',
                'date_processed': datetime.now().strftime('%Y-%m-%d'),
                'source_path': str(file_path.relative_to(self.base_path)),
                'notes': 'Native video conversion',
                'native_pair_id': base_id
            }
            
            image_record = {
                'unique_id': f"{base_id}-IMG",
                'original_filename': file_path.name,
                'new_filename': image_filename,
                'creator_name': metadata.get('creator_name', ''),
                'language': metadata.get('language', ''),
                'category': metadata.get('category', ''),
                'content_type': metadata.get('content_type', ''),
                'creative_type': 'native_image',
                'duration_seconds': 0,
                'aspect_ratio': '16:9',  # Native images are 640x360 = 16:9
                'width_px': 640,
                'height_px': 360,
                'file_size_mb': 0.5 if self.dry_run else round(Path(image_path).stat().st_size / (1024 * 1024), 2),
                'file_format': 'png',
                'date_processed': datetime.now().strftime('%Y-%m-%d'),
                'source_path': str(file_path.relative_to(self.base_path)),
                'notes': 'Native image thumbnail',
                'native_pair_id': base_id
            }
            
            return [video_record, image_record]
            
        except Exception as e:
            print(f"  ✗ Error processing native pair: {e}")
            return []
    
    def process_file(self, file_path):
        """Process a single file"""
        print(f"\n{'='*80}")
        print(f"Processing: {file_path.name}")
        
        # Skip hidden files and non-media files
        if file_path.name.startswith('.'):
            print("SKIPPED: Hidden file")
            return None
        
        ext = file_path.suffix.lower()
        if ext not in self.video_extensions and ext not in self.image_extensions:
            print(f"SKIPPED: Unsupported file type: {ext}")
            return None
        
        # Check if file was already processed (unless force_reprocess is enabled)
        source_path = str(file_path.relative_to(self.base_path))
        if not self.force_reprocess and source_path in self.existing_files:
            print("SKIPPED: Already processed")
            print("         (use --force-reprocess to reprocess this file)")
            self.skipped_count += 1
            return None
        
        # Generate unique ID
        unique_id = self.generate_unique_id()
        print(f"Unique ID: {unique_id}")
        
        # Extract technical metadata
        if ext in self.video_extensions:
            tech_metadata = self.get_video_metadata(file_path)
            print(f"Video metadata: {tech_metadata['duration_seconds']}s, {tech_metadata['width_px']}x{tech_metadata['height_px']}")
        else:
            tech_metadata = self.get_image_metadata(file_path)
            print(f"Image metadata: {tech_metadata['width_px']}x{tech_metadata['height_px']}")
        
        # Parse filename
        parsed_data = self.parse_structured_filename(file_path.name)
        if parsed_data:
            print(f"Detected Pattern 1 (Structured)")
        elif self.parse_simple_filename(file_path.name):
            print(f"Detected Pattern 2 (Simple)")
        else:
            print(f"WARNING: Filename doesn't match known patterns")
        
        # Resolve metadata
        metadata, notes = self.resolve_metadata(file_path, parsed_data)
        print(f"Metadata resolved: {notes}")
        
        # Classify creative type
        creative_type = self.classify_creative_type(file_path, tech_metadata)
        print(f"Creative type: {creative_type}")
        
        # Check if this file will be processed as native
        will_process_native = (self.force_native or self._is_native_file(file_path)) and ext in self.video_extensions
        
        # Generate new filename (pass duration for videos)
        # Add ORG_ prefix if this is an original that will be converted to native
        duration = tech_metadata.get('duration_seconds', 0) if ext in self.video_extensions else None
        new_filename = self.generate_new_filename(unique_id, metadata, ext, duration, is_native_original=will_process_native)
        print(f"New filename: {new_filename}")
        
        # Get file size
        file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
        
        # Build inventory record
        record = {
            'unique_id': unique_id,
            'original_filename': file_path.name,
            'new_filename': new_filename,
            'creator_name': metadata.get('creator_name', ''),
            'language': metadata.get('language', ''),
            'category': metadata.get('category', ''),
            'content_type': metadata.get('content_type', ''),
            'creative_type': creative_type,
            'duration_seconds': tech_metadata['duration_seconds'],
            'aspect_ratio': tech_metadata['aspect_ratio'],
            'width_px': tech_metadata['width_px'],
            'height_px': tech_metadata['height_px'],
            'file_size_mb': file_size_mb,
            'file_format': ext.replace('.', ''),
            'date_processed': datetime.now().strftime('%Y-%m-%d'),
            'source_path': str(file_path.relative_to(self.base_path)),
            'notes': notes,
            'native_pair_id': ''  # Empty for non-native files
        }
        
        # Process native format if determined above (will_process_native)
        native_records = []
        if will_process_native:
            native_records = self._process_native_pair(
                file_path, unique_id, metadata, tech_metadata
            )
        
        # Move/rename file
        if not self.dry_run:
            new_path = self.upload_dir / new_filename
            # Handle duplicate filenames
            counter = 1
            while new_path.exists():
                base = new_filename.rsplit('.', 1)[0]
                new_filename_dup = f"{base}_dup{counter}.{ext.replace('.', '')}"
                new_path = self.upload_dir / new_filename_dup
                counter += 1
            
            file_path.rename(new_path)
            self._save_processed_id(unique_id)
            print(f"✓ Moved to: {new_path.relative_to(self.base_path)}")
        else:
            print(f"[DRY RUN] Would move to: uploaded/{new_filename}")
        
        # Return list of records (original + native pair if applicable)
        if native_records:
            return [record] + native_records
        return record
    
    def process_all_files(self):
        """Process all files in source_files directory"""
        print(f"\n{'='*80}")
        print(f"Creative Asset Processor - {'DRY RUN MODE' if self.dry_run else 'PROCESSING MODE'}")
        print(f"{'='*80}")
        print(f"Base path: {self.base_path}")
        print(f"Source directory: {self.source_dir}")
        print(f"Upload directory: {self.upload_dir}")
        print(f"Metadata defaults loaded: {len(self.metadata_defaults)} folders")
        if self.force_reprocess:
            print(f"Force reprocess: ENABLED (will reprocess all files)")
        else:
            print(f"Duplicate detection: ENABLED (skips already processed files)")
        if self.force_native:
            print(f"Native mode: FORCED (will process ALL videos as native ads)")
        elif self.native_mode:
            print(f"Native folder detected: Will process files in source_files/native/ as native ads")
        print(f"{'='*80}\n")
        
        if not self.source_dir.exists():
            print(f"ERROR: Source directory does not exist: {self.source_dir}")
            return
        
        # Find all files recursively
        all_files = []
        for ext in list(self.video_extensions) + list(self.image_extensions):
            all_files.extend(self.source_dir.rglob(f"*{ext}"))
        
        # Count how many files are already processed
        already_processed = 0
        if not self.force_reprocess and self.existing_files:
            for file_path in all_files:
                source_path = str(file_path.relative_to(self.base_path))
                if source_path in self.existing_files:
                    already_processed += 1
        
        print(f"Found {len(all_files)} media file(s)")
        if already_processed > 0 and not self.force_reprocess:
            new_files = len(all_files) - already_processed
            print(f"  - {already_processed} already processed (will skip)")
            print(f"  - {new_files} new file(s) to process")
            print(f"\n💡 Use --force-reprocess to reprocess all files\n")
        else:
            print()
        
        if len(all_files) == 0:
            print("No files to process. Add files to source_files/ directory.")
            return
        
        # Process each file
        for file_path in all_files:
            try:
                records = self.process_file(file_path)
                if records:
                    # Handle both single record and list of records (native pairs)
                    if isinstance(records, list):
                        self.inventory_data.extend(records)
                    else:
                        self.inventory_data.append(records)
            except Exception as e:
                print(f"ERROR processing {file_path.name}: {e}")
                continue
        
        # Save any new folder defaults
        if self.new_folders_added and not self.dry_run:
            self._save_metadata_defaults()
        
        # Clean up empty folders
        if not self.dry_run:
            self._cleanup_empty_folders()
        
        # Generate CSV
        if self.inventory_data:
            df_session = pd.DataFrame(self.inventory_data)
            
            if not self.dry_run:
                # Save session CSV (current run only)
                df_session.to_csv(self.session_csv, index=False)
                
                # Append to master CSV (cumulative inventory)
                if self.output_csv.exists():
                    # Load existing master inventory
                    df_master = pd.read_csv(self.output_csv)
                    # Append new records
                    df_combined = pd.concat([df_master, df_session], ignore_index=True)
                    df_combined.to_csv(self.output_csv, index=False)
                else:
                    # Create new master inventory
                    df_session.to_csv(self.output_csv, index=False)
                
                print(f"\n{'='*80}")
                print(f"✓ Processing complete!")
                print(f"✓ Processed {len(self.inventory_data)} new file(s)")
                if self.skipped_count > 0:
                    print(f"✓ Skipped {self.skipped_count} already-processed file(s)")
                print(f"✓ Files moved to: uploaded/")
                print(f"✓ Session CSV: {self.session_csv.relative_to(self.base_path)}")
                print(f"✓ Master CSV: {self.output_csv.relative_to(self.base_path)}")
                if self.new_folders_added:
                    print(f"✓ Added {len(self.new_folders_added)} new folder(s) to metadata defaults")
                print(f"✓ Empty source folders cleaned up")
                print(f"{'='*80}\n")
            else:
                print(f"\n{'='*80}")
                print(f"[DRY RUN] Would process {len(self.inventory_data)} file(s)")
                if self.skipped_count > 0:
                    print(f"[DRY RUN] Would skip {self.skipped_count} already-processed file(s)")
                print(f"[DRY RUN] Would save session CSV to: {self.session_csv.relative_to(self.base_path)}")
                print(f"[DRY RUN] Would append to master CSV: {self.output_csv.relative_to(self.base_path)}")
                print(f"{'='*80}\n")
            
            # Print summary (for current session)
            self.print_summary(df_session)
    
    def print_summary(self, df):
        """Print processing summary statistics"""
        print("\n--- SUMMARY ---")
        print(f"\nTotal files: {len(df)}")
        
        print(f"\nBy Creative Type:")
        for ctype, count in df['creative_type'].value_counts().items():
            print(f"  {ctype}: {count}")
        
        print(f"\nBy Creator:")
        for creator, count in df['creator_name'].value_counts().items():
            print(f"  {creator}: {count}")
        
        print(f"\nBy Category:")
        for category, count in df['category'].value_counts().items():
            print(f"  {category}: {count}")
        
        print(f"\nBy Content Type:")
        for ctype, count in df['content_type'].value_counts().items():
            print(f"  {ctype}: {count}")
        
        # Files needing review
        needs_review = df[df['notes'].str.contains('NEEDS MANUAL REVIEW', na=False)]
        if len(needs_review) > 0:
            print(f"\n⚠️  Files needing manual review: {len(needs_review)}")
            for idx, row in needs_review.iterrows():
                print(f"    - {row['original_filename']}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Creative Asset Processor')
    parser.add_argument('--dry-run', action='store_true', help='Preview processing without making changes')
    parser.add_argument('--no-interactive', action='store_true', help='Disable interactive prompts for unknown folders')
    parser.add_argument('--force-reprocess', action='store_true', help='Reprocess files even if already in inventory CSV')
    parser.add_argument('--native', action='store_true', help='Force native processing for ALL videos (normally only processes files in source_files/native/)')
    parser.add_argument('--path', default=None, help='Base path for Creative Flow project (defaults to parent of script directory)')
    
    args = parser.parse_args()
    
    # If no path specified, use parent directory of script location
    if args.path is None:
        script_dir = Path(__file__).resolve().parent
        base_path = script_dir.parent
    else:
        base_path = args.path
    
    processor = CreativeProcessor(
        base_path, 
        dry_run=args.dry_run, 
        interactive=not args.no_interactive,
        force_reprocess=args.force_reprocess,
        native=args.native
    )
    processor.process_all_files()


if __name__ == '__main__':
    main()

