#!/usr/bin/env python3
"""
Test script for file validation and error recovery
Tests the robust validation system with various file types
"""
import asyncio
import tempfile
import os
from utils.file_validator import VideoFileValidator

async def test_file_validation():
    """Test the file validation system"""
    print("Testing File Validation System...")
    print("=" * 50)
    
    # Test 1: Valid video file (create a small test video)
    print("\n1. Testing valid video file...")
    try:
        import cv2
        import numpy as np
        
        # Create a small test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        out = cv2.VideoWriter(temp_path, fourcc, 10.0, (320, 240))
        for i in range(30):  # 3 second video
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
            out.write(frame)
        out.release()
        
        # Read and validate
        with open(temp_path, 'rb') as f:
            content = f.read()
        
        is_valid, message = VideoFileValidator.validate_file(content, "test_video.mp4")
        print(f"   Valid video: {is_valid} - {message}")
        
        if is_valid:
            info = VideoFileValidator.get_video_info(content, "test_video.mp4")
            print(f"   Video info: {info['width']}x{info['height']}, {info['duration_seconds']:.1f}s")
        
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"   Error creating test video: {e}")
    
    # Test 2: Invalid file extension
    print("\n2. Testing invalid file extension...")
    fake_content = b"This is not a video file"
    is_valid, message = VideoFileValidator.validate_file(fake_content, "test.txt")
    print(f"   Text file: {is_valid} - {message}")
    
    # Test 3: Wrong magic bytes
    print("\n3. Testing wrong magic bytes...")
    fake_video = b"FAKE" + b"0" * 1000  # Fake content with wrong magic bytes
    is_valid, message = VideoFileValidator.validate_file(fake_video, "fake.mp4")
    print(f"   Fake MP4: {is_valid} - {message}")
    
    # Test 4: File too small
    print("\n4. Testing file too small...")
    tiny_file = b"mp4"
    is_valid, message = VideoFileValidator.validate_file(tiny_file, "tiny.mp4")
    print(f"   Tiny file: {is_valid} - {message}")
    
    # Test 5: Suspicious filename
    print("\n5. Testing suspicious filename...")
    is_valid, message = VideoFileValidator.validate_file(fake_content, "../../../etc/passwd.mp4")
    print(f"   Path traversal: {is_valid} - {message}")
    
    print("\n" + "=" * 50)
    print("File validation tests completed!")

async def test_memory_monitoring():
    """Test memory monitoring"""
    print("\nTesting Memory Monitoring...")
    print("=" * 30)
    
    try:
        from cv_pipeline.video_processor import VideoProcessor
        
        processor = VideoProcessor()
        memory_usage = processor._check_memory_usage()
        print(f"Current memory usage: {memory_usage:.1f}MB")
        
        # Test memory cleanup
        processor.detections_history = [{"frame": i, "data": "x" * 1000} for i in range(2000)]
        print(f"Added test data, memory: {processor._check_memory_usage():.1f}MB")
        
        processor._cleanup_memory()
        print(f"After cleanup, memory: {processor._check_memory_usage():.1f}MB")
        print(f"Detection history length: {len(processor.detections_history)}")
        
    except Exception as e:
        print(f"Memory monitoring test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_file_validation())
    asyncio.run(test_memory_monitoring())
