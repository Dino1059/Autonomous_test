import os
import re
from PIL import Image
import argparse
from pathlib import Path
import cv2
import numpy as np


def natural_sort_key(filename):
    """
    Sort filenames naturally, handling any number of digits properly
    Examples: 1.png, 2.png, ..., 10.png, 11.png, 20.png, 100.png
    """
    # Split filename into text and numeric parts
    parts = re.split(r'(\d+)', filename)
    # Convert numeric parts to integers for proper sorting
    result = []
    for part in parts:
        if part.isdigit():
            result.append(int(part))
        else:
            result.append(part.lower())
    return result


def test_natural_sorting():
    """Test function to verify natural sorting works correctly"""
    test_files = ['1.png', '2.png', '10.png', '11.png', '20.png', '100.png', '3.png', '21.png']
    sorted_files = sorted(test_files, key=natural_sort_key)
    print("Natural sorting test:")
    print(f"Original: {test_files}")
    print(f"Sorted:   {sorted_files}")
    expected = ['1.png', '2.png', '3.png', '10.png', '11.png', '20.png', '21.png', '100.png']
    print(f"Expected: {expected}")
    print(f"✅ Test {'PASSED' if sorted_files == expected else 'FAILED'}")
    return sorted_files == expected


def generate_gif_from_screenshots(input_folder, output_path=None, duration=500, loop=0):
    """
    Generate a GIF from screenshots in a folder
    
    Args:
        input_folder (str): Path to folder containing screenshots
        output_path (str): Output GIF file path. If None, saves as 'animation.gif' in input folder
        duration (int): Duration between frames in milliseconds (default: 500ms)
        loop (int): Number of loops (0 = infinite loop)
    
    Returns:
        str: Path to generated GIF file
    """
    input_path = Path(input_folder)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input folder does not exist: {input_folder}")
    
    # Find all image files (png, jpg, jpeg)
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    image_files = []
    
    for file in input_path.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            image_files.append(file)
    
    if not image_files:
        raise ValueError(f"No image files found in {input_folder}")
    
    # Sort files naturally
    image_files.sort(key=lambda x: natural_sort_key(x.name))
    
    print(f"Found {len(image_files)} images:")
    for img_file in image_files:
        print(f"  - {img_file.name}")
    
    # Load images
    images = []
    for img_file in image_files:
        try:
            img = Image.open(img_file)
            # Convert to RGB if necessary (for GIF compatibility)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
            print(f"Loaded: {img_file.name} ({img.size})")
        except Exception as e:
            print(f"Warning: Could not load {img_file.name}: {e}")
    
    if not images:
        raise ValueError("No valid images could be loaded")
    
    # Set output path
    if output_path is None:
        output_path = input_path / 'animation.gif'
    else:
        output_path = Path(output_path)
    
    # Create GIF
    print(f"\nGenerating GIF: {output_path}")
    print(f"Frame duration: {duration}ms")
    print(f"Loop count: {'infinite' if loop == 0 else loop}")
    
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop,
        optimize=True
    )
    
    print(f"✅ GIF generated successfully: {output_path}")
    return str(output_path)


def generate_video_from_screenshots(input_folder, output_path=None, fps=2):
    """
    Generate a video (MP4) from screenshots in a folder
    
    Args:
        input_folder (str): Path to folder containing screenshots
        output_path (str): Output video file path. If None, saves as 'animation.mp4' in input folder
        fps (float): Frames per second (default: 2)
    
    Returns:
        str: Path to generated video file
    """
    input_path = Path(input_folder)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input folder does not exist: {input_folder}")
    
    # Find all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    image_files = []
    
    for file in input_path.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            image_files.append(file)
    
    if not image_files:
        raise ValueError(f"No image files found in {input_folder}")
    
    # Sort files naturally
    image_files.sort(key=lambda x: natural_sort_key(x.name))
    
    print(f"Found {len(image_files)} images:")
    for img_file in image_files:
        print(f"  - {img_file.name}")
    
    # Set output path
    if output_path is None:
        output_path = input_path / 'animation.mp4'
    else:
        output_path = Path(output_path)
    
    # Read first image to get dimensions
    first_img = cv2.imread(str(image_files[0]))
    if first_img is None:
        raise ValueError(f"Could not read first image: {image_files[0]}")
    
    height, width, layers = first_img.shape
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    print(f"\nGenerating video: {output_path}")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    
    # Add frames to video
    for i, img_file in enumerate(image_files):
        img = cv2.imread(str(img_file))
        if img is not None:
            # Resize if necessary
            if img.shape[:2] != (height, width):
                img = cv2.resize(img, (width, height))
            video_writer.write(img)
            print(f"Added frame {i+1}/{len(image_files)}: {img_file.name}")
        else:
            print(f"Warning: Could not load {img_file.name}")
    
    # Release video writer
    video_writer.release()
    cv2.destroyAllWindows()
    
    print(f"✅ Video generated successfully: {output_path}")
    return str(output_path)


def generate_from_screenshots(input_folder, output_path=None, format_type='gif', duration=500, fps=2, loop=0):
    """
    Generate GIF or video from screenshots in a folder
    
    Args:
        input_folder (str): Path to folder containing screenshots
        output_path (str): Output file path. If None, auto-generates based on format
        format_type (str): 'gif' or 'video' (default: 'gif')
        duration (int): Duration between frames in milliseconds for GIF (default: 500ms)
        fps (float): Frames per second for video (default: 2)
        loop (int): Number of loops for GIF (0 = infinite loop)
    
    Returns:
        str: Path to generated file
    """
    if format_type.lower() == 'gif':
        return generate_gif_from_screenshots(input_folder, output_path, duration, loop)
    elif format_type.lower() == 'video':
        return generate_video_from_screenshots(input_folder, output_path, fps)
    else:
        raise ValueError(f"Unsupported format: {format_type}. Use 'gif' or 'video'")


def main():
    parser = argparse.ArgumentParser(description='Generate GIF or video from screenshots in a folder')
    parser.add_argument('input_folder', nargs='?', help='Path to folder containing screenshots')
    parser.add_argument('-o', '--output', help='Output file path (default: auto-generated based on format)')
    parser.add_argument('-f', '--format', choices=['gif', 'video'], default='gif', help='Output format: gif or video (default: gif)')
    parser.add_argument('-d', '--duration', type=int, default=500, help='Duration between frames in milliseconds for GIF (default: 500)')
    parser.add_argument('--fps', type=float, default=2, help='Frames per second for video (default: 2)')
    parser.add_argument('-l', '--loop', type=int, default=0, help='Number of loops for GIF (0 = infinite, default: 0)')
    parser.add_argument('--test', action='store_true', help='Run natural sorting test')
    
    args = parser.parse_args()
    
    # Run test if requested
    if args.test:
        print("Running natural sorting test...")
        test_passed = test_natural_sorting()
        return 0 if test_passed else 1
    
    # Check if input folder is provided
    if not args.input_folder:
        parser.error("input_folder is required when not running test")
    
    try:
        output_path = generate_from_screenshots(
            args.input_folder,
            args.output,
            args.format,
            args.duration,
            args.fps,
            args.loop
        )
        print(f"\n🎉 Success! {args.format.upper()} saved at: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
