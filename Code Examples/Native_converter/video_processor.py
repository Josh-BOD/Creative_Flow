#!/usr/bin/env python3
"""
Video Processing Script
Processes all MP4 files in the INPUT folder:
1. Resizes videos to 640x360 resolution
2. Extracts the first frame as a PNG
3. Names the output files as "Batch 1 - video x.png"
"""

import os
import cv2
import glob
from pathlib import Path

def process_videos():
    """Process all MP4 files in the INPUT folder"""
    
    # Define input and output directories
    input_dir = Path("INPUT")
    output_dir = Path("OUTPUT")
    output_videos_dir = Path("OUTPUT/videos")
    
    # Create output directories if they don't exist
    output_dir.mkdir(exist_ok=True)
    output_videos_dir.mkdir(exist_ok=True)
    
    # Get all MP4 files from INPUT directory
    video_files = glob.glob(str(input_dir / "*.mp4"))
    
    if not video_files:
        print("No MP4 files found in INPUT directory")
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    # Process each video file
    for idx, video_path in enumerate(sorted(video_files), 1):
        video_filename = os.path.basename(video_path)
        # Remove .mp4 extension to get base name
        base_name = os.path.splitext(video_filename)[0]
        print(f"Processing video {idx}: {video_filename}")
        
        try:
            # Open the video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print(f"Error: Could not open video {video_filename}")
                continue
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            max_frames = int(fps * 4)  # Only process first 4 seconds
            
            # Read the first frame to get dimensions
            ret, frame = cap.read()
            
            if not ret:
                print(f"Error: Could not read first frame from {video_filename}")
                cap.release()
                continue
            
            # Get original dimensions
            height, width = frame.shape[:2]
            target_width, target_height = 640, 360
            target_aspect = target_width / target_height
            original_aspect = width / height
            
            # Calculate crop parameters
            if original_aspect > target_aspect:
                # Image is wider - crop width
                new_width = int(height * target_aspect)
                start_x = (width - new_width) // 2
                crop_params = (0, height, start_x, start_x + new_width)  # (start_y, end_y, start_x, end_x)
            else:
                # Image is taller - crop height
                new_height = int(width / target_aspect)
                start_y = (height - new_height) // 2
                crop_params = (start_y, start_y + new_height, 0, width)  # (start_y, end_y, start_x, end_x)
            
            # Reset video to beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Set up video writer for output video
            output_video_filename = f"{base_name}.mp4"
            output_video_path = output_videos_dir / output_video_filename
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (target_width, target_height))
            
            # Process first frame for PNG
            cropped_frame = frame[crop_params[0]:crop_params[1], crop_params[2]:crop_params[3]]
            resized_frame = cv2.resize(cropped_frame, (target_width, target_height))
            
            # Save first frame as PNG with compression
            output_png_filename = f"{base_name}.png"
            output_png_path = output_dir / output_png_filename
            # PNG compression level: 0-9 (0=no compression, 9=max compression)
            compression_params = [cv2.IMWRITE_PNG_COMPRESSION, 8]
            png_success = cv2.imwrite(str(output_png_path), resized_frame, compression_params)
            
            # Write first frame to video
            out.write(resized_frame)
            
            # Process remaining frames (up to 4 seconds)
            frame_num = 1
            while frame_num < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Crop and resize frame
                cropped_frame = frame[crop_params[0]:crop_params[1], crop_params[2]:crop_params[3]]
                resized_frame = cv2.resize(cropped_frame, (target_width, target_height))
                
                # Write frame to output video
                out.write(resized_frame)
                frame_num += 1
            
            # Release everything
            cap.release()
            out.release()
            
            if png_success:
                print(f"✓ Saved PNG: {output_png_filename}")
            else:
                print(f"✗ Failed to save PNG: {output_png_filename}")
                
            duration = frame_num / fps if fps > 0 else 0
            print(f"✓ Saved Video: {output_video_filename} ({frame_num} frames, {duration:.1f}s)")
            
        except Exception as e:
            print(f"Error processing {video_filename}: {str(e)}")
    
    print(f"\nProcessing complete! Check the OUTPUT folder for PNG thumbnails and OUTPUT/videos folder for processed videos.")

def main():
    """Main function"""
    print("Video Processing Script")
    print("=" * 50)
    
    # Check if INPUT directory exists
    if not os.path.exists("INPUT"):
        print("Error: INPUT directory not found!")
        print("Please ensure the INPUT directory exists in the current working directory.")
        return
    
    # Process the videos
    process_videos()

if __name__ == "__main__":
    main()
