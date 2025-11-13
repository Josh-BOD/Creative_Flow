"""
Creative Flow Upload Manager

Manages file uploads to advertising platforms (TrafficJunky, Exoclick, etc.)
"""

import argparse
import sys
import time
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Playwright not installed. Run: ./setup_upload.sh")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv not installed. Run: ./setup_upload.sh")
    sys.exit(1)

from uploaders.tj_auth import TJAuthenticator
from uploaders.tj_uploader import TJUploader


class UploadManager:
    """Manages creative file uploads across platforms."""
    
    def __init__(self, base_path: Path, config: Dict):
        """
        Initialize Upload Manager.
        
        Args:
            base_path: Base directory path (Creative Flow folder)
            config: Configuration dictionary
        """
        self.base_path = base_path
        self.config = config
        
        # Directories
        self.uploaded_dir = base_path / "uploaded"
        self.tracking_dir = base_path / "tracking"
        self.archive_dir = base_path / "archive"
        self.session_dir = base_path / "data" / "session"
        
        # Upload logs subdirectory (keeps tracking folder clean)
        self.upload_logs_dir = self.tracking_dir / "upload_logs"
        self.screenshot_dir = self.upload_logs_dir / "screenshots"
        self.upload_csv_dir = self.tracking_dir / "Upload_CSV"
        
        # Ensure directories exist
        for directory in [self.tracking_dir, self.archive_dir, self.upload_logs_dir, 
                          self.screenshot_dir, self.session_dir, self.upload_csv_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Session CSV path
        self.session_csv = self.tracking_dir / "creative_inventory_session.csv"
        self.master_csv = self.tracking_dir / "creative_inventory.csv"
        
        # TJ Creative Library cache (for fast duplicate detection)
        self.tj_library_csv = self.tracking_dir / "TJ_Creative_Library.csv"
        self.tj_library_cache = {}  # filename -> creative_id mapping
        
        # Logger
        self.logger = self._setup_logger()
        
        # Load TJ Creative Library cache
        self._load_tj_library_cache()
        
        # Upload status tracking
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.upload_status_csv = self.upload_logs_dir / f"upload_status_{timestamp}.csv"
        self.upload_results = []
        
        # Batch tracking
        self.batch_id = self._get_next_batch_id()
    
    def _load_tj_library_cache(self):
        """
        Load TJ Creative Library cache from CSV for fast duplicate detection.
        
        This cache maps filenames to Creative IDs that already exist on TJ.
        Much faster than scraping pagination every time.
        """
        try:
            if not self.tj_library_csv.exists():
                self.logger.info("TJ Creative Library cache not found (will be created on first upload)")
                return
            
            import pandas as pd
            df = pd.read_csv(self.tj_library_csv)
            
            # Build filename -> creative_id mapping
            for _, row in df.iterrows():
                filename = row.get('filename')
                creative_id = row.get('creative_id')
                if filename and creative_id:
                    self.tj_library_cache[filename] = str(creative_id)
            
            self.logger.info(f"✓ Loaded {len(self.tj_library_cache)} Creative IDs from TJ Library cache")
            
        except Exception as e:
            self.logger.warning(f"Could not load TJ Library cache: {e}")
            self.tj_library_cache = {}
    
    def _check_tj_library_duplicate(self, filename: str) -> Optional[str]:
        """
        Check if filename already exists in TJ Creative Library.
        
        Args:
            filename: Name of file to check
            
        Returns:
            Creative ID if exists, None if not found
        """
        return self.tj_library_cache.get(filename)
    
    def _update_tj_library_cache(self, filename: str, creative_id: str, file_type: str = '', 
                                  creative_type: str = '', dimensions: str = ''):
        """
        Add a new Creative ID to the TJ Library cache.
        
        Args:
            filename: Name of the uploaded file
            creative_id: The Creative ID from TJ
            file_type: File extension (e.g., 'mp4', 'png')
            creative_type: Type of creative (e.g., 'native_video')
            dimensions: Dimensions (e.g., '640x360')
        """
        try:
            import pandas as pd
            
            # Add to in-memory cache
            self.tj_library_cache[filename] = creative_id
            
            # Append to CSV file
            new_row = {
                'creative_id': creative_id,
                'filename': filename,
                'upload_date': datetime.now().strftime('%Y-%m-%d'),
                'dimensions': dimensions,
                'file_type': file_type,
                'creative_type': creative_type,
                'review_status': 'pending'
            }
            
            # If CSV doesn't exist, create with header
            if not self.tj_library_csv.exists():
                df = pd.DataFrame([new_row])
                df.to_csv(self.tj_library_csv, index=False)
            else:
                # Append to existing CSV
                df = pd.DataFrame([new_row])
                df.to_csv(self.tj_library_csv, mode='a', header=False, index=False)
            
            self.logger.debug(f"Added to TJ Library cache: {filename} → {creative_id}")
            
        except Exception as e:
            self.logger.warning(f"Could not update TJ Library cache: {e}")
    
    def _get_next_batch_id(self) -> str:
        """
        Get the next batch ID by checking existing Upload_CSV files.
        
        Returns:
            Batch ID as string (e.g., "001")
        """
        try:
            # Find all existing batch CSVs
            existing_csvs = list(self.upload_csv_dir.glob("Batch*_*.csv"))
            
            if not existing_csvs:
                return "001"
            
            # Extract batch numbers
            batch_numbers = []
            for csv_file in existing_csvs:
                # Format: Batch001_Date_Time_Type.csv
                parts = csv_file.stem.split('_')
                if parts and parts[0].startswith('Batch'):
                    try:
                        batch_num = int(parts[0].replace('Batch', ''))
                        batch_numbers.append(batch_num)
                    except ValueError:
                        continue
            
            if batch_numbers:
                next_batch = max(batch_numbers) + 1
                return f"{next_batch:03d}"
            else:
                return "001"
                
        except Exception as e:
            self.logger.warning(f"Error getting batch ID: {e}, defaulting to 001")
            return "001"
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for upload manager."""
        logger = logging.getLogger('upload_manager')
        logger.setLevel(logging.DEBUG if self.config.get('verbose') else logging.INFO)
        
        # Clear existing handlers
        logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if self.config.get('verbose') else logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (save to upload_logs subdirectory)
        log_file = self.upload_logs_dir / f"upload_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def load_files_from_session(self) -> List[Dict]:
        """
        Load files to upload from session CSV.
        
        Returns:
            List of file records to upload
        """
        import pandas as pd
        
        if not self.session_csv.exists():
            self.logger.error(f"Session CSV not found: {self.session_csv}")
            return []
        
        try:
            df = pd.read_csv(self.session_csv)
            self.logger.info(f"Loaded {len(df)} records from session CSV")
            
            # Filter out ORG_ files (original native files, not for upload)
            df_filtered = df[~df['new_filename'].str.startswith('ORG_', na=False)]
            self.logger.info(f"After filtering ORG_ files: {len(df_filtered)} records")
            
            # Convert to list of dicts
            files = df_filtered.to_dict('records')
            return files
            
        except Exception as e:
            self.logger.error(f"Error loading session CSV: {e}")
            return []
    
    def validate_file(self, file_record: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate that a file exists and is ready for upload.
        
        Args:
            file_record: File record dictionary from CSV
            
        Returns:
            (is_valid, error_message)
        """
        new_filename = file_record.get('new_filename')
        
        if not new_filename:
            return False, "Missing filename"
        
        # Determine file path based on creative_type
        creative_type = file_record.get('creative_type', '')
        
        if 'native_video' in creative_type:
            file_path = self.uploaded_dir / "Native" / "Video" / new_filename
        elif 'native_image' in creative_type:
            file_path = self.uploaded_dir / "Native" / "Image" / new_filename
        elif 'video' in creative_type or 'short_video' in creative_type:
            file_path = self.uploaded_dir / "Video" / new_filename
        elif 'image' in creative_type:
            file_path = self.uploaded_dir / "Image" / new_filename
        else:
            file_path = self.uploaded_dir / new_filename
        
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Check file size for native images (TrafficJunky max: 300KB decimal)
        if 'native_image' in creative_type:
            file_size_bytes = file_path.stat().st_size
            file_size_kb = file_size_bytes / 1000  # Decimal KB (like Mac Finder)
            
            if file_size_kb > 300:
                return False, f"Native image too large: {file_size_kb:.1f}KB (max 300KB)"
        
        return True, None
    
    def _get_file_path(self, file_record: Dict) -> Optional[Path]:
        """Get the full file path for a file record."""
        new_filename = file_record.get('new_filename')
        creative_type = file_record.get('creative_type', '')
        
        if 'native_video' in creative_type:
            return self.uploaded_dir / "Native" / "Video" / new_filename
        elif 'native_image' in creative_type:
            return self.uploaded_dir / "Native" / "Image" / new_filename
        elif 'video' in creative_type or 'short_video' in creative_type:
            return self.uploaded_dir / "Video" / new_filename
        elif 'image' in creative_type:
            return self.uploaded_dir / "Image" / new_filename
        else:
            return self.uploaded_dir / new_filename
    
    def _save_upload_result(self, file_record: Dict, status: str, creative_id: Optional[str] = None, error: Optional[str] = None):
        """Save upload result for later CSV export."""
        result = {
            'unique_id': file_record.get('unique_id', ''),
            'file_name': file_record.get('new_filename', ''),
            'file_path': str(self._get_file_path(file_record)) if self._get_file_path(file_record) else '',
            'upload_date': datetime.now().strftime('%Y-%m-%d'),
            'upload_time': datetime.now().strftime('%H:%M:%S'),
            'platform': 'TrafficJunky',
            'tj_creative_id': creative_id or '',
            'status': status,
            'error_message': error or '',
            'creative_type': file_record.get('creative_type', ''),
            'native_pair_id': file_record.get('native_pair_id', ''),
            'retries': 0
        }
        self.upload_results.append(result)
    
    def _save_upload_status_csv(self):
        """Save all upload results to CSV."""
        if not self.upload_results:
            return
        
        try:
            import pandas as pd
            df = pd.DataFrame(self.upload_results)
            df.to_csv(self.upload_status_csv, index=False)
            self.logger.info(f"✓ Upload status saved to: {self.upload_status_csv.name}")
        except Exception as e:
            self.logger.error(f"Failed to save upload status CSV: {e}")
    
    def _update_master_csv(self):
        """Update master CSV with Creative IDs."""
        import pandas as pd
        
        try:
            # Load master CSV
            if not self.master_csv.exists():
                self.logger.warning("Master CSV not found, skipping Creative ID update")
                return
            
            df_master = pd.read_csv(self.master_csv)
            
            # Add tj_creative_id column if it doesn't exist
            if 'tj_creative_id' not in df_master.columns:
                df_master['tj_creative_id'] = ''
                df_master['tj_upload_date'] = ''
            
            # Update with new Creative IDs
            updated_count = 0
            for result in self.upload_results:
                if result['status'] == 'success' and result['tj_creative_id']:
                    mask = df_master['unique_id'] == result['unique_id']
                    if mask.any():
                        df_master.loc[mask, 'tj_creative_id'] = result['tj_creative_id']
                        df_master.loc[mask, 'tj_upload_date'] = result['upload_date']
                        updated_count += 1
            
            # Save updated master CSV
            if updated_count > 0:
                df_master.to_csv(self.master_csv, index=False)
                self.logger.info(f"✓ Updated {updated_count} Creative IDs in master CSV")
            else:
                self.logger.info("No Creative IDs to update in master CSV")
                
        except Exception as e:
            self.logger.error(f"Failed to update master CSV: {e}")
    
    def _generate_tj_tool_csvs(self):
        """Generate TJ_tool compatible CSVs for campaign uploads."""
        import pandas as pd
        
        try:
            # Load master CSV with Creative IDs
            if not self.master_csv.exists():
                self.logger.warning("Master CSV not found, skipping TJ_tool CSV generation")
                return
            
            df = pd.read_csv(self.master_csv)
            
            # Filter only files with TJ Creative IDs (uploaded)
            df_uploaded = df[df['tj_creative_id'].notna() & (df['tj_creative_id'] != '')]
            
            if df_uploaded.empty:
                self.logger.info("No uploaded files with Creative IDs to export")
                return
            
            # Generate timestamp and batch ID for naming
            date_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            batch_id = self.batch_id
            
            # === GENERATE NATIVE CSV ===
            # Filter native videos and images (VID_ and IMG_ prefixes)
            native_videos = df_uploaded[df_uploaded['new_filename'].str.startswith('VID_', na=False)].copy()
            native_images = df_uploaded[df_uploaded['new_filename'].str.startswith('IMG_', na=False)].copy()
            
            if not native_videos.empty and not native_images.empty:
                # Extract base ID (strip -VID and -IMG suffixes)
                native_videos['base_id'] = native_videos['unique_id'].str.replace('-VID', '', regex=False)
                native_images['base_id'] = native_images['unique_id'].str.replace('-IMG', '', regex=False)
                
                # Merge video and image pairs on base_id
                native_pairs = pd.merge(
                    native_videos[['base_id', 'tj_creative_id', 'new_filename', 'category']],
                    native_images[['base_id', 'tj_creative_id']],
                    on='base_id',
                    suffixes=('_video', '_image')
                )
                
                if not native_pairs.empty:
                    # Create Native CSV in TJ_tool format
                    native_csv = pd.DataFrame({
                        'Ad Name': native_pairs['new_filename'].str.replace('.mp4', '', regex=False),
                        'Target URL': 'PLACEHOLDER_URL',  # User will fill this in
                        'Video Creative ID': native_pairs['tj_creative_id_video'].astype(int),
                        'Thumbnail Creative ID': native_pairs['tj_creative_id_image'].astype(int),
                        'Headline': native_pairs['category'].fillna('PLACEHOLDER_HEADLINE'),
                        'Brand Name': 'PLACEHOLDER_BRAND'
                    })
                    
                    # Save with proper naming: Batch{id}_Date_Time_Native.csv
                    native_csv_path = self.upload_csv_dir / f"Batch{batch_id}_{date_time}_Native.csv"
                    native_csv.to_csv(native_csv_path, index=False, quoting=1)  # quoting=1 quotes all fields
                    self.logger.info(f"✓ Generated Native CSV: {native_csv_path.name} ({len(native_csv)} pairs)")
            
            # === GENERATE PREROLL CSV ===
            # Filter regular files (no IMG_, VID_, or ORG_ prefixes)
            preroll_files = df_uploaded[
                ~df_uploaded['new_filename'].str.startswith(('IMG_', 'VID_', 'ORG_'), na=False)
            ].copy()
            
            if not preroll_files.empty:
                # Create Preroll CSV in TJ_tool format
                preroll_csv = pd.DataFrame({
                    'Ad Name': preroll_files['new_filename'].str.replace(r'\.(mp4|jpg|png|gif)$', '', regex=True),
                    'Target URL': 'PLACEHOLDER_URL',  # User will fill this in
                    'Creative ID': preroll_files['tj_creative_id'].astype(int),
                    'Custom CTA Text': 'PLACEHOLDER_CTA',
                    'Custom CTA URL': 'PLACEHOLDER_URL',
                    'Banner CTA Creative ID': '',
                    'Banner CTA Title': '',
                    'Banner CTA Subtitle': '',
                    'Banner CTA URL': '',
                    'Tracking Pixel': ''
                })
                
                # Save with proper naming: Batch{id}_Date_Time_Preroll.csv
                preroll_csv_path = self.upload_csv_dir / f"Batch{batch_id}_{date_time}_Preroll.csv"
                preroll_csv.to_csv(preroll_csv_path, index=False)
                self.logger.info(f"✓ Generated Preroll CSV: {preroll_csv_path.name} ({len(preroll_csv)} files)")
            
            self.logger.info("✓ TJ_tool CSVs generated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to generate TJ_tool CSVs: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _group_files_by_type(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Group files by creative type for batch uploading."""
        groups = {
            'native_video': [],
            'native_image': [],
            'video': [],
            'image': []
        }
        
        for file_record in files:
            creative_type = file_record.get('creative_type', '').lower()
            
            if 'native_video' in creative_type:
                groups['native_video'].append(file_record)
            elif 'native_image' in creative_type:
                groups['native_image'].append(file_record)
            elif 'video' in creative_type or 'short_video' in creative_type:
                groups['video'].append(file_record)
            elif 'image' in creative_type:
                groups['image'].append(file_record)
        
        return groups
    
    def upload_to_trafficjunky(self, files: List[Dict]) -> Dict:
        """
        Upload files to TrafficJunky.
        
        Args:
            files: List of file records to upload
            
        Returns:
            Upload summary dictionary
        """
        summary = {
            'total': len(files),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
        
        self.logger.info("="*60)
        self.logger.info("Starting TrafficJunky Upload Process")
        self.logger.info("="*60)
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=self.config.get('headless', False),
                    slow_mo=self.config.get('slow_mo', 100)
                )
                
                self.logger.info("Browser launched")
                
                # Initialize authenticator
                authenticator = TJAuthenticator(
                    self.config['tj_username'],
                    self.config['tj_password'],
                    session_dir=self.session_dir
                )
                
                # Try to load saved session
                context = authenticator.load_session(browser)
                
                if context:
                    page = context.new_page()
                    page.set_default_timeout(self.config.get('timeout', 30000))
                    
                    self.logger.info("Checking if saved session is still valid...")
                    page.goto('https://advertiser.trafficjunky.com/media-library', wait_until='domcontentloaded')
                    
                    if authenticator.is_logged_in(page):
                        self.logger.info("✓ Logged in using saved session")
                    else:
                        self.logger.warning("Saved session expired, need to login again")
                        context.close()
                        context = None
                
                # If no valid session, do manual login
                if not context:
                    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                    page = context.new_page()
                    page.set_default_timeout(self.config.get('timeout', 30000))
                    
                    self.logger.info("No valid session found, manual login required...")
                    
                    if not authenticator.manual_login(page, timeout=120):
                        self.logger.error("Authentication failed or timed out")
                        browser.close()
                        return summary
                    
                    # Save session for future use
                    authenticator.save_session(context)
                    self.logger.info("✓ Logged into TrafficJunky (session saved)")
                
                # Initialize uploader
                uploader = TJUploader(
                    dry_run=self.config.get('dry_run', True),
                    take_screenshots=self.config.get('take_screenshots', True)
                )
                
                # Group files by creative type for batch uploading
                groups = self._group_files_by_type(files)
                
                # Apply limit if specified (for testing) - BEFORE processing batches
                # This ensures native video/image pairs have matching IDs
                limit = self.config.get('limit')
                if limit:
                    self.logger.info(f"\nApplying limit of {limit} files per batch...")
                    
                    # For native pairs, get the unique IDs from videos and filter images to match
                    if groups['native_video'] and groups['native_image']:
                        # Limit native videos
                        limited_native_videos = groups['native_video'][:limit]
                        # Extract base IDs from the limited videos (strip -VID suffix)
                        video_base_ids = set()
                        for f in limited_native_videos:
                            uid = f.get('unique_id', '')
                            # Strip -VID suffix to get base ID (e.g., ID-6BCC9A21-VID -> ID-6BCC9A21)
                            base_id = uid.replace('-VID', '') if uid.endswith('-VID') else uid
                            video_base_ids.add(base_id)
                        
                        # Filter images to only include matching base IDs
                        matching_images = []
                        for f in groups['native_image']:
                            uid = f.get('unique_id', '')
                            # Strip -IMG suffix to get base ID
                            base_id = uid.replace('-IMG', '') if uid.endswith('-IMG') else uid
                            if base_id in video_base_ids:
                                matching_images.append(f)
                        
                        groups['native_image'] = matching_images
                        groups['native_video'] = limited_native_videos
                        
                        self.logger.info(f"  Native pairs: {len(groups['native_video'])} videos + {len(groups['native_image'])} matching images")
                        self.logger.info(f"  Base IDs: {', '.join(sorted(video_base_ids))}")
                    
                    # Limit other groups normally
                    if groups['video']:
                        groups['video'] = groups['video'][:limit]
                        self.logger.info(f"  Regular videos: {len(groups['video'])} files")
                    if groups['image']:
                        groups['image'] = groups['image'][:limit]
                        self.logger.info(f"  Regular images: {len(groups['image'])} files")
                
                # Define upload order
                group_order = ['native_video', 'native_image', 'video', 'image']
                
                # IMPORTANT: Limit batch size to avoid pagination issues
                # TJ Media Library shows 12 creatives per page, so uploading 10 at a time
                # keeps us within a single page and simplifies duplicate detection
                MAX_BATCH_SIZE = 10
                
                batch_number = 0
                
                # Process each group
                for group_name in group_order:
                    group_files = groups[group_name]
                    
                    if not group_files:
                        continue
                    
                    # Split large groups into chunks of MAX_BATCH_SIZE
                    total_files = len(group_files)
                    chunks = [group_files[i:i + MAX_BATCH_SIZE] for i in range(0, total_files, MAX_BATCH_SIZE)]
                    
                    for chunk_idx, chunk_files in enumerate(chunks, 1):
                        batch_number += 1
                        chunk_info = f" (chunk {chunk_idx}/{len(chunks)})" if len(chunks) > 1 else ""
                        self.logger.info(f"\n{'='*60}")
                        self.logger.info(f"BATCH {batch_number}: {group_name.upper()} ({len(chunk_files)}/{total_files} files{chunk_info})")
                        self.logger.info(f"{'='*60}")
                        
                        # Validate files and filter duplicates
                        valid_files = []
                        valid_file_paths = []
                        
                        for file_record in chunk_files:
                            # Validate file exists
                            is_valid, error = self.validate_file(file_record)
                            if not is_valid:
                                self.logger.error(f"Skipping {file_record.get('new_filename')}: {error}")
                                summary['skipped'] += 1
                                self._save_upload_result(file_record, 'skipped', error=error)
                                continue
                            
                            # Check for duplicate in master CSV
                            if not self.config.get('force') and file_record.get('tj_creative_id'):
                                self.logger.info(f"Skipping {file_record.get('new_filename')}: Already uploaded (ID: {file_record.get('tj_creative_id')})")
                                summary['skipped'] += 1
                                self._save_upload_result(file_record, 'skipped',
                                                        creative_id=file_record.get('tj_creative_id'),
                                                        error='Already uploaded (use --force to re-upload)')
                                continue
                            
                            # Check for duplicate in TJ Library cache (fast local check)
                            filename = file_record.get('new_filename')
                            cached_id = self._check_tj_library_duplicate(filename)
                            if not self.config.get('force') and cached_id:
                                self.logger.info(f"Skipping {filename}: Already exists on TJ (ID: {cached_id} from cache)")
                                summary['skipped'] += 1
                                self._save_upload_result(file_record, 'skipped',
                                                        creative_id=cached_id,
                                                        error='Already exists on TJ (from library cache)')
                                continue
                            
                            # File is valid and should be uploaded
                            valid_files.append(file_record)
                            valid_file_paths.append(self._get_file_path(file_record))
                        
                        if not valid_files:
                            self.logger.info(f"No files to upload in this batch (all skipped)")
                            continue
                        
                        # Show files in this batch
                        self.logger.info(f"Files in batch:")
                        for i, f in enumerate(valid_files, 1):
                            self.logger.info(f"  [{i}] {f.get('new_filename')}")
                        
                        # Upload batch with retry logic
                        max_retries = 3
                        upload_result = None
                        
                        for attempt in range(max_retries):
                            if attempt > 0:
                                self.logger.info(f"\nRetry attempt {attempt}/{max_retries-1}")
                                import time
                                time.sleep(2)
                            
                            # Create screenshot directory for this batch
                            screenshot_dir = self.screenshot_dir / f"batch_{batch_number:02d}_{group_name}"
                            
                            # Perform batch upload
                            upload_result = uploader.upload_creative_batch(
                                page=page,
                                file_paths=valid_file_paths,
                                screenshot_dir=screenshot_dir,
                                creative_type=group_name
                            )
                            
                            # Check result
                            if upload_result['status'] == 'success':
                                # Match Creative IDs to files
                                creative_ids = upload_result.get('creative_ids', [])
                                self.logger.info(f"\n✓ Batch upload successful! {len(creative_ids)} Creative IDs extracted")
                                
                                # Save results for each file
                                for i, (file_record, creative_id) in enumerate(zip(valid_files, creative_ids)):
                                    self.logger.info(f"  [{i+1}] {file_record.get('new_filename')} → {creative_id}")
                                    summary['successful'] += 1
                                    self._save_upload_result(file_record, 'success', creative_id=creative_id)
                                    
                                    # Update TJ Library cache with new Creative ID
                                    filename = file_record.get('new_filename')
                                    file_type = file_record.get('file_type', '')
                                    creative_type = file_record.get('creative_type', '')
                                    dimensions = file_record.get('dimensions', '')
                                    self._update_tj_library_cache(filename, creative_id, file_type, creative_type, dimensions)
                                
                                # Handle files without IDs (shouldn't happen, but just in case)
                                if len(creative_ids) < len(valid_files):
                                    self.logger.warning(f"⚠ Only got {len(creative_ids)} IDs for {len(valid_files)} files")
                                    for i in range(len(creative_ids), len(valid_files)):
                                        file_record = valid_files[i]
                                        self.logger.warning(f"  No ID for: {file_record.get('new_filename')}")
                                        summary['failed'] += 1
                                        self._save_upload_result(file_record, 'failed',
                                                                error='Creative ID not extracted')
                                
                                summary['results'].append(upload_result)
                                break
                                
                            elif upload_result['status'] == 'duplicate':
                                # Files already exist on TJ (no new Creative IDs created)
                                self.logger.warning(f"\n⚠ No new Creative IDs - files may already exist on TJ:")
                                for file_record in valid_files:
                                    self.logger.warning(f"  - {file_record.get('new_filename')} (duplicate or already uploaded)")
                                    summary['skipped'] += 1
                                    self._save_upload_result(file_record, 'duplicate',
                                                            error='File already exists on TJ (no new Creative ID)')
                                summary['results'].append(upload_result)
                                break
                                
                            elif upload_result['status'] == 'dry_run_success':
                                self.logger.info(f"✓ Dry-run successful for batch (no actual upload)")
                                for file_record in valid_files:
                                    summary['skipped'] += 1
                                    self._save_upload_result(file_record, 'dry_run')
                                summary['results'].append(upload_result)
                                break
                                
                            else:
                                # Failed, will retry
                                self.logger.warning(f"Batch upload failed: {upload_result.get('error', 'Unknown error')}")
                                if attempt == max_retries - 1:
                                    # Final attempt failed
                                    self.logger.error(f"✗ Batch upload failed after {max_retries} attempts")
                                    for file_record in valid_files:
                                        summary['failed'] += 1
                                        self._save_upload_result(file_record, 'failed',
                                                                error=upload_result.get('error'))
                                    summary['results'].append(upload_result)
                
                # Close browser
                browser.close()
                self.logger.info("Browser closed")
                
                # Save upload status CSV
                self._save_upload_status_csv()
                
                # Update master CSV with Creative IDs
                if summary['successful'] > 0:
                    self._update_master_csv()
                    
                    # Generate TJ_tool compatible CSVs
                    self._generate_tj_tool_csvs()
        
        except Exception as e:
            self.logger.error(f"Fatal error during upload: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            # Always save upload status, even if there was an error
            self._save_upload_status_csv()
        
        return summary
    
    def print_summary(self, summary: Dict):
        """Print upload summary."""
        print("\n" + "="*60)
        print("UPLOAD SUMMARY")
        print("="*60)
        print(f"Total files:      {summary['total']}")
        print(f"Successful:       {summary['successful']}")
        print(f"Failed:           {summary['failed']}")
        print(f"Skipped:          {summary['skipped']}")
        print("="*60)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Creative Flow Upload Manager - Upload creatives to advertising platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload files from session CSV (dry-run)
  python3 scripts/upload_manager.py --session
  
  # Upload files from session CSV (live mode)
  python3 scripts/upload_manager.py --session --live
  
  # Upload specific files
  python3 scripts/upload_manager.py --files "file1.mp4,file2.jpg"
  
  # Upload with headless browser
  python3 scripts/upload_manager.py --session --headless
  
  # Force re-upload even if Creative ID exists
  python3 scripts/upload_manager.py --session --force
  
  # Verbose output
  python3 scripts/upload_manager.py --session --verbose
        """
    )
    
    parser.add_argument(
        '--session',
        action='store_true',
        help='Upload files from session CSV'
    )
    
    parser.add_argument(
        '--files',
        type=str,
        help='Comma-separated list of files to upload'
    )
    
    parser.add_argument(
        '--live',
        action='store_true',
        help='Disable dry-run mode and perform actual uploads (default: dry-run)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-upload even if Creative ID already exists'
    )
    
    parser.add_argument(
        '--platform',
        type=str,
        default='tj',
        choices=['tj', 'exo'],
        help='Upload platform (default: tj - TrafficJunky)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of files per batch (for testing, e.g., --limit 2)'
    )
    
    parser.add_argument(
        '--tj-username',
        type=str,
        help='TrafficJunky username (overrides config)'
    )
    
    parser.add_argument(
        '--tj-password',
        type=str,
        help='TrafficJunky password (overrides config)'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Determine base path
    base_path = Path(__file__).resolve().parent.parent
    
    # Load environment variables from .env file
    env_file = base_path / "config" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print("✓ Loaded configuration from config/.env")
    else:
        print("⚠️  No .env file found, using environment variables or command line args")
    
    # Load configuration from environment variables or args
    config = {
        'dry_run': not args.live if args.live else os.getenv('DRY_RUN', 'True').lower() == 'true',
        'headless': args.headless if args.headless else os.getenv('HEADLESS_MODE', 'False').lower() == 'true',
        'take_screenshots': os.getenv('TAKE_SCREENSHOTS', 'True').lower() == 'true',
        'verbose': args.verbose,
        'force': args.force,
        'limit': args.limit,
        'timeout': int(os.getenv('TIMEOUT', '30000')),
        'slow_mo': int(os.getenv('SLOW_MO', '100')),
        'tj_username': args.tj_username or os.getenv('TJ_USERNAME', 'PLACEHOLDER'),
        'tj_password': args.tj_password or os.getenv('TJ_PASSWORD', 'PLACEHOLDER')
    }
    
    # Validate credentials
    if config['tj_username'] == 'PLACEHOLDER' or config['tj_password'] == 'PLACEHOLDER':
        print("\nERROR: TrafficJunky credentials not configured!")
        print("\nSetup instructions:")
        print("1. Copy config/env_template.txt to config/.env")
        print("2. Edit config/.env and add your TJ username and password")
        print("3. OR use --tj-username and --tj-password flags")
        print("4. OR set TJ_USERNAME and TJ_PASSWORD environment variables")
        return 1
    
    # Create Upload Manager
    manager = UploadManager(base_path, config)
    
    print("="*60)
    print("Creative Flow Upload Manager")
    print("="*60)
    print(f"Platform: {args.platform.upper()}")
    print(f"Mode: {'LIVE' if not config['dry_run'] else 'DRY-RUN'}")
    print(f"Headless: {'Yes' if config['headless'] else 'No'}")
    print(f"Force: {'Yes' if config['force'] else 'No'}")
    if config.get('limit'):
        print(f"Limit: {config['limit']} files per batch (TESTING MODE)")
    print("="*60)
    print()
    
    # Load files to upload
    if args.session:
        manager.logger.info("Loading files from session CSV...")
        files = manager.load_files_from_session()
        
        if not files:
            manager.logger.error("No files to upload from session CSV")
            return 1
        
        manager.logger.info(f"Found {len(files)} files to upload")
    elif args.files:
        # TODO: Parse individual files from comma-separated list
        manager.logger.error("--files option not yet implemented")
        return 1
    else:
        print("ERROR: Must specify --session or --files")
        return 1
    
    # Upload to platform
    if args.platform == 'tj':
        summary = manager.upload_to_trafficjunky(files)
    else:
        manager.logger.error(f"Platform {args.platform} not yet implemented")
        return 1
    
    # Print summary
    manager.print_summary(summary)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

