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

