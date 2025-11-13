#!/usr/bin/env python3
"""
Native Creative Converter
Converts videos to TrafficJunky native ad format:
- 640x360 resolution with center-crop
- Maximum 4 seconds duration
- Extracts first frame as PNG thumbnail
"""

import subprocess
from pathlib import Path
from PIL import Image
import io
import cv2


class NativeConverter:
    """Handles conversion of videos to native ad format using ffmpeg"""
    
    def __init__(self, target_width=640, target_height=360, max_duration=4.0):
        """
        Initialize native converter.
        
        Args:
            target_width: Target video width (default: 640)
            target_height: Target video height (default: 360)
            max_duration: Maximum video duration in seconds (default: 4.0)
        """
        self.target_width = target_width
        self.target_height = target_height
        self.max_duration = max_duration
        self.target_aspect = target_width / target_height
    
    def convert_video(self, input_path, output_video_path, output_image_path):
        """
        Convert video to native format and extract thumbnail using ffmpeg.
        
        Args:
            input_path: Path to source video file
            output_video_path: Path for output video (640x360, 4sec max)
            output_image_path: Path for output PNG thumbnail
            
        Returns:
            dict with {
                'success': bool,
                'duration': float,
                'error': str (if failed)
            }
        """
        try:
            input_path = Path(input_path)
            output_video_path = Path(output_video_path)
            output_image_path = Path(output_image_path)
            
            # Ensure output directories exist
            output_video_path.parent.mkdir(parents=True, exist_ok=True)
            output_image_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get video properties using ffprobe
            duration_cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(input_path)
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            original_duration = float(duration_result.stdout.strip()) if duration_result.stdout.strip() else 0
            
            width_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(input_path)
            ]
            width_result = subprocess.run(width_cmd, capture_output=True, text=True)
            original_width = int(width_result.stdout.strip()) if width_result.stdout.strip() else 0
            
            height_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=height', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(input_path)
            ]
            height_result = subprocess.run(height_cmd, capture_output=True, text=True)
            original_height = int(height_result.stdout.strip()) if height_result.stdout.strip() else 0
            
            if not original_width or not original_height:
                return {'success': False, 'error': 'Could not get original video dimensions.'}
            
            # Calculate crop filter for center-crop to 16:9
            original_aspect = original_width / original_height
            
            if original_aspect > self.target_aspect:
                # Original is wider, crop width
                new_width_after_crop = int(original_height * self.target_aspect)
                crop_filter = f"crop={new_width_after_crop}:{original_height}:(iw-{new_width_after_crop})/2:0"
            else:
                # Original is taller, crop height
                new_height_after_crop = int(original_width / self.target_aspect)
                crop_filter = f"crop={original_width}:{new_height_after_crop}:0:(ih-{new_height_after_crop})/2"
            
            # FFmpeg command to crop, resize, set duration
            ffmpeg_command = [
                'ffmpeg',
                '-i', str(input_path),
                '-ss', '0',  # Start from beginning
                '-t', str(self.max_duration),  # Limit duration
                '-vf', f"{crop_filter},scale={self.target_width}:{self.target_height}",
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',  # Overwrite output files without asking
                str(output_video_path)
            ]
            
            # Command to extract first frame as PNG
            thumbnail_command = [
                'ffmpeg',
                '-i', str(input_path),
                '-ss', '00:00:00.000',
                '-vframes', '1',
                '-vf', f"{crop_filter},scale={self.target_width}:{self.target_height}",
                '-y',
                str(output_image_path)
            ]
            
            # Run video conversion
            video_process = subprocess.run(ffmpeg_command, capture_output=True, text=True)
            if video_process.returncode != 0:
                return {'success': False, 'error': f"FFmpeg video conversion failed: {video_process.stderr}"}
            
            # Run thumbnail extraction
            thumbnail_process = subprocess.run(thumbnail_command, capture_output=True, text=True)
            if thumbnail_process.returncode != 0:
                return {'success': False, 'error': f"FFmpeg thumbnail extraction failed: {thumbnail_process.stderr}"}
            
            # Compress image to be under 300KB for TrafficJunky native ads
            compress_result = self._compress_image_to_max_size(output_image_path, max_size_kb=300)
            if not compress_result['success']:
                return {'success': False, 'error': f"Image compression failed: {compress_result['error']}"}
            
            # Log compression results
            if compress_result.get('original_size_kb') != compress_result.get('final_size_kb'):
                print(f"    Image compressed: {compress_result['original_size_kb']}KB → {compress_result['final_size_kb']}KB", end='')
                if compress_result.get('converted_to_jpeg'):
                    print(f" (converted to JPEG, quality={compress_result.get('quality', 85)})", end='')
                if compress_result.get('resized'):
                    print(f" (resized to {compress_result.get('new_dimensions')})", end='')
                print()
            
            # Get actual duration of the converted video
            converted_duration_cmd = [
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                str(output_video_path)
            ]
            converted_duration_result = subprocess.run(converted_duration_cmd, capture_output=True, text=True)
            converted_duration = float(converted_duration_result.stdout.strip()) if converted_duration_result.stdout.strip() else 0
            
            return {'success': True, 'duration': round(converted_duration, 2)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _compress_image_to_max_size(self, image_path, max_size_kb=300):
        """
        Compress a PNG image to be under the specified size using OpenCV PNG compression (like original).
        
        Args:
            image_path: Path to the PNG image
            max_size_kb: Maximum file size in kilobytes (default: 300)
            
        Returns:
            dict with {'success': bool, 'final_size_kb': float, 'error': str}
        """
        try:
            image_path = Path(image_path)
            
            # Check initial size (use decimal KB: 1000 bytes = 1KB, like Mac Finder and TrafficJunky)
            file_size_bytes = image_path.stat().st_size
            initial_size_kb = file_size_bytes / 1000  # Decimal KB
            max_size_bytes = max_size_kb * 1000  # Convert to bytes using decimal
            
            if file_size_bytes <= max_size_bytes:
                return {
                    'success': True,
                    'final_size_kb': round(initial_size_kb, 2),
                    'original_size_kb': round(initial_size_kb, 2)
                }
            
            # Load image with OpenCV (same as original code)
            img = cv2.imread(str(image_path))
            
            if img is None:
                return {'success': False, 'error': 'Could not read image'}
            
            # Try OpenCV PNG compression levels (like original: level 8)
            # PNG compression: 0=no compression, 9=max compression (lossless)
            for compression_level in [8, 9]:  # Try level 8 first (original), then max
                compression_params = [cv2.IMWRITE_PNG_COMPRESSION, compression_level]
                success = cv2.imwrite(str(image_path), img, compression_params)
                
                if not success:
                    continue
                
                file_size_bytes = image_path.stat().st_size
                
                if file_size_bytes <= max_size_bytes:
                    return {
                        'success': True,
                        'final_size_kb': round(file_size_bytes / 1000, 2),
                        'original_size_kb': round(initial_size_kb, 2),
                        'compression_level': compression_level
                    }
            
            # If PNG compression isn't enough, convert to JPEG
            # Try progressively lower JPEG quality
            for quality in range(95, 50, -5):
                jpeg_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                temp_path = image_path.with_suffix('.jpg')
                success = cv2.imwrite(str(temp_path), img, jpeg_params)
                
                if not success:
                    continue
                
                file_size_bytes = temp_path.stat().st_size
                
                if file_size_bytes <= max_size_bytes:
                    # Rename JPEG to .png extension for consistency
                    temp_path.rename(image_path)
                    
                    return {
                        'success': True,
                        'final_size_kb': round(file_size_bytes / 1000, 2),
                        'original_size_kb': round(initial_size_kb, 2),
                        'converted_to_jpeg': True,
                        'quality': quality
                    }
                else:
                    # Clean up temp file if too large
                    temp_path.unlink()
            
            # If still too large, resize the image
            scale_factor = (max_size_bytes / file_size_bytes) ** 0.5
            new_width = int(img.shape[1] * scale_factor * 0.9)  # 90% to be safe
            new_height = int(img.shape[0] * scale_factor * 0.9)
            
            img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            # Save resized image as JPEG
            jpeg_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
            cv2.imwrite(str(image_path), img_resized, jpeg_params)
            
            final_size_bytes = image_path.stat().st_size
            
            return {
                'success': True,
                'final_size_kb': round(final_size_bytes / 1000, 2),
                'original_size_kb': round(initial_size_kb, 2),
                'converted_to_jpeg': True,
                'resized': True,
                'new_dimensions': f"{new_width}x{new_height}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

