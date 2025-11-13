Native Conversion Integration Plan
Overview
Integrate native creative conversion into the existing Creative Flow asset processor to generate video/image pairs for TrafficJunky native ad uploads.

Requirements Summary
Native Processing Specs:

Video: 640x360 resolution, 4-second duration max
Image: 640x360 PNG thumbnail (first frame)
Naming: VID_ and IMG_ prefixes with shared ID
Output: uploaded/Native/Video/ and uploaded/Native/Image/
Trigger: --native flag OR files in source_files/native/ folder
Naming Convention Changes:

Original: EN_Ahegao_NSFW_Generic_Seras_5sec_ID-0AE9FF9D.mp4
Native Video: VID_EN_Ahegao_NSFW_Generic_Seras_5sec_ID-0AE9FF9D-VID.mp4
Native Image: IMG_EN_Ahegao_NSFW_Generic_Seras_ID-0AE9FF9D-IMG.png
Implementation
1. Add Native Conversion Module
File: [scripts/native_converter.py](scripts/native_converter.py) (NEW)

Based on [Code Examples/Native_converter/video_processor.py](Code Examples/Native_converter/video_processor.py), create a module that:

Resizes videos to 640x360 with center-crop
Limits duration to 4 seconds
Extracts first frame as PNG thumbnail
Uses OpenCV (cv2) for processing
Key Functions:

class NativeConverter:
    def convert_video(self, input_path, output_video_path, output_image_path):
        # Resize to 640x360, crop to maintain aspect ratio
        # Limit to 4 seconds max
        # Save first frame as PNG
        # Return success/failure status
2. Update Main Processor
File: [scripts/creative_processor.py](scripts/creative_processor.py)

Changes needed:

a) Add command-line flag:

parser.add_argument('--native', action='store_true', 
                   help='Process files for native ad format (640x360 video + thumbnail)')
b) Add native folder detection in __init__:

self.native_mode = native or self._detect_native_folder()

def _detect_native_folder(self):
    """Check if processing files from source_files/native/ folder"""
    # Return True if any files are in native subfolder
c) Add native output directories:

self.native_video_dir = self.upload_dir / "Native" / "Video"
self.native_image_dir = self.upload_dir / "Native" / "Image"
# Create directories in __init__ if native_mode is True
d) Modify process_file() method:

def process_file(self, file_path):
    # ... existing processing ...
    
    if self.native_mode and ext in self.video_extensions:
        # Generate native pair with shared ID
        native_results = self._process_native_pair(
            file_path, unique_id, metadata, tech_metadata
        )
        # Add native records to inventory
        self.inventory_data.extend(native_results)
    
    # ... continue with normal processing ...
e) Add native processing method:

def _process_native_pair(self, file_path, base_id, metadata, tech_metadata):
    """
    Process video for native format, creating video + image pair.
    
    Returns: List of 2 records (video and image) for CSV
    """
    from native_converter import NativeConverter
    
    converter = NativeConverter()
    
    # Generate filenames with VID_/IMG_ prefixes and -VID/-IMG suffixes
    video_filename = self._generate_native_filename(
        base_id, metadata, 'VID', tech_metadata['duration_seconds']
    )
    image_filename = self._generate_native_filename(
        base_id, metadata, 'IMG', None
    )
    
    video_path = self.native_video_dir / video_filename
    image_path = self.native_image_dir / image_filename
    
    # Convert using native_converter
    success = converter.convert_video(file_path, video_path, image_path)
    
    # Create inventory records for both
    video_record = {
        'unique_id': f"{base_id}-VID",
        'original_filename': file_path.name,
        'new_filename': video_filename,
        'creative_type': 'native_video',
        # ... copy other metadata ...
        'native_pair_id': base_id,
        'width_px': 640,
        'height_px': 360,
        'duration_seconds': 4.0,  # or actual duration if less
    }
    
    image_record = {
        'unique_id': f"{base_id}-IMG",
        'original_filename': file_path.name,
        'new_filename': image_filename,
        'creative_type': 'native_image',
        # ... copy other metadata ...
        'native_pair_id': base_id,
        'width_px': 640,
        'height_px': 360,
        'duration_seconds': 0,
    }
    
    return [video_record, image_record]
f) Add native filename generator:

def _generate_native_filename(self, unique_id, metadata, prefix, duration_seconds=None):
    """
    Generate filename with VID_/IMG_ prefix and -VID/-IMG suffix.
    
    Args:
        prefix: 'VID' or 'IMG'
        duration_seconds: Include for videos, None for images
    """
    parts = [
        prefix,
        metadata.get('language', 'UNK'),
        metadata.get('category', 'UNK'),
        metadata.get('content_type', 'UNK'),
        metadata.get('creative_name', 'Generic'),
        metadata.get('creator_name', 'UNK')
    ]
    
    if duration_seconds is not None:
        duration_sec = int(round(duration_seconds))
        parts.append(f"{duration_sec}sec")
    
    # Add unique ID with suffix
    parts.append(f"{unique_id}-{prefix}")
    
    # Sanitize and join
    sanitized = [re.sub(r'[^a-zA-Z0-9-]', '', str(p)) for p in parts]
    
    ext = '.mp4' if prefix == 'VID' else '.png'
    return '_'.join(sanitized) + ext
3. Add Dependencies
File: [requirements.txt](requirements.txt)

Add OpenCV requirement:

opencv-python==4.8.1.78
4. Update CSV Schema
File: [scripts/creative_processor.py](scripts/creative_processor.py)

Add new columns to inventory CSV:

native_pair_id: Shared ID for video/image pairs (empty for non-native)
Update creative_type to include: native_video, native_image
5. Update Documentation
File: [HOW_TO_USE.md](HOW_TO_USE.md)

Add section:

## Native Creative Processing

Process videos for TrafficJunky native ads (640x360 video + thumbnail pairs):

### Option 1: Use --native flag
python3 scripts/creative_processor.py --native

### Option 2: Place files in native subfolder
source_files/
└── native/
    ├── video1.mp4
    └── video2.mp4

### Output Structure
uploaded/
├── Native/
│   ├── Video/
│   │   └── VID_EN_Ahegao_NSFW_Generic_Seras_4sec_ID-ABC123-VID.mp4
│   └── Image/
│       └── IMG_EN_Ahegao_NSFW_Generic_Seras_ID-ABC123-IMG.png

### Naming Convention
- Prefix: VID_ for videos, IMG_ for images
- Suffix: -VID for videos, -IMG for images
- Shared base ID for matching pairs
- Videos: 640x360, max 4 seconds
- Images: 640x360 PNG (first frame)
Testing Strategy
Test native flag:
python3 scripts/creative_processor.py --native --dry-run
Test native folder detection:
Place test videos in source_files/native/
Run without --native flag
Verify automatic detection
Verify output:
Check uploaded/Native/Video/ contains 640x360 MP4s
Check uploaded/Native/Image/ contains matching PNGs
Verify CSV has paired IDs
Test with existing workflow:
Process mixed native and regular files
Verify regular files go to uploaded/
Verify native files go to uploaded/Native/
File Changes Summary
New Files:

scripts/native_converter.py - Native conversion logic
TODO/plan2.md - This plan document
Modified Files:

scripts/creative_processor.py - Add native processing
requirements.txt - Add opencv-python
HOW_TO_USE.md - Document native mode
Future Enhancements (Not in this plan)
GIF_ prefix for animated GIFs
IFRA_ prefix for iframe embeds
Multiple output sizes (configurable dimensions)
Direct upload to TrafficJunky Media Library
