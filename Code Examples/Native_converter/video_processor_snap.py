#!/usr/bin/env python3
"""
Video Processing Script - Snap Resize
Processes all MP4 files in the INPUT folder:
1. Resizes videos from 480x864 to 540x950 (slight stretch)
2. Uses Lanczos interpolation for high-quality scaling
3. Saves resized videos to OUTPUT/videos folder
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
    
    # Target dimensions
    target_width, target_height = 540, 950
    
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
            
            # Read the first frame to get dimensions
            ret, frame = cap.read()
            
            if not ret:
                print(f"Error: Could not read first frame from {video_filename}")
                cap.release()
                continue
            
            # Get original dimensions
            height, width = frame.shape[:2]
            print(f"  Original dimensions: {width}x{height}")
            print(f"  Target dimensions: {target_width}x{target_height}")
            
            # Reset video to beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Set up video writer for output video
            output_video_filename = f"{base_name}_540x950.mp4"
            output_video_path = output_videos_dir / output_video_filename
            
            # Use H.264 codec (avc1 is the fourcc code for H.264)
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (target_width, target_height))
            
            if not out.isOpened():
                print(f"Error: Could not create video writer for {output_video_filename}")
                cap.release()
                continue
            
            # Process all frames
            frame_num = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize frame using Lanczos interpolation (high quality)
                # cv2.INTER_LANCZOS4 is equivalent to ffmpeg's lanczos flag
                resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
                
                # Write frame to output video
                out.write(resized_frame)
                frame_num += 1
                
                # Print progress every 30 frames
                if frame_num % 30 == 0:
                    print(f"  Processing frame {frame_num}/{frame_count}...", end='\r')
            
            # Release everything
            cap.release()
            out.release()
            
            duration = frame_num / fps if fps > 0 else 0
            print(f"✓ Saved Video: {output_video_filename} ({frame_num} frames, {duration:.1f}s)")
            
        except Exception as e:
            print(f"Error processing {video_filename}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\nProcessing complete! Check the OUTPUT/videos folder for resized videos.")

def main():
    """Main function"""
    print("Video Processing Script - Snap Resize (480x864 → 540x950)")
    print("=" * 60)
    
    # Check if INPUT directory exists
    if not os.path.exists("INPUT"):
        print("Error: INPUT directory not found!")
        print("Please ensure the INPUT directory exists in the current working directory.")
        return
    
    # Process the videos
    process_videos()

if __name__ == "__main__":
    main()

