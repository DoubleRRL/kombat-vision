"""
Robust file validation to prevent non-video uploads from breaking the tool
Uses multiple validation layers: extension, magic bytes, and OpenCV verification
"""
import os
import cv2
import tempfile
from typing import Tuple, Optional
from pathlib import Path


class FileValidationError(Exception):
    """Custom exception for file validation failures"""
    pass


class VideoFileValidator:
    """
    Multi-layer video file validation system
    Prevents crashes from malicious or corrupted files
    """
    
    # Video file magic bytes (first few bytes that identify file type)
    VIDEO_MAGIC_BYTES = {
        b'\x00\x00\x00\x18ftypmp4': 'MP4',
        b'\x00\x00\x00\x20ftypmp4': 'MP4', 
        b'RIFF': 'AVI',
        b'\x1a\x45\xdf\xa3': 'MKV/WebM',
        b'ftyp': 'MOV/MP4',
        b'\x00\x00\x00\x14ftyp': 'MOV'
    }
    
    ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB limit
    MIN_FILE_SIZE = 1024  # 1KB minimum
    
    @classmethod
    def validate_file(cls, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Comprehensive file validation
        Returns (is_valid, error_message)
        """
        try:
            # 1. Basic checks
            cls._validate_filename(filename)
            cls._validate_file_size(file_content)
            
            # 2. Magic byte validation
            cls._validate_magic_bytes(file_content)
            
            # 3. OpenCV validation (most important - actually tries to open as video)
            cls._validate_with_opencv(file_content, filename)
            
            return True, "Valid video file"
            
        except FileValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation failed: {str(e)}"
    
    @classmethod
    def _validate_filename(cls, filename: str) -> None:
        """Validate filename and extension"""
        if not filename:
            raise FileValidationError("No filename provided")
        
        # Check for suspicious characters
        suspicious_chars = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        if any(char in filename for char in suspicious_chars):
            raise FileValidationError("Filename contains suspicious characters")
        
        # Check extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file extension: {file_ext}. "
                f"Allowed: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )
    
    @classmethod
    def _validate_file_size(cls, file_content: bytes) -> None:
        """Validate file size is reasonable"""
        file_size = len(file_content)
        
        if file_size < cls.MIN_FILE_SIZE:
            raise FileValidationError(
                f"File too small: {file_size} bytes. Minimum: {cls.MIN_FILE_SIZE} bytes"
            )
        
        if file_size > cls.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            raise FileValidationError(
                f"File too large: {size_mb:.1f}MB. Maximum: {max_mb:.0f}MB"
            )
    
    @classmethod
    def _validate_magic_bytes(cls, file_content: bytes) -> None:
        """Check file magic bytes to verify it's actually a video file"""
        if len(file_content) < 32:
            raise FileValidationError("File too small to contain valid video headers")
        
        # Check first 32 bytes for known video signatures
        header = file_content[:32]
        
        # Look for any known video magic bytes
        is_video = False
        for magic_bytes, file_type in cls.VIDEO_MAGIC_BYTES.items():
            if magic_bytes in header:
                is_video = True
                break
        
        # Additional checks for common video patterns
        if not is_video:
            # Check for ftyp box (MP4/MOV)
            if b'ftyp' in header[:20]:
                is_video = True
            # Check for RIFF header (AVI)
            elif header.startswith(b'RIFF') and b'AVI ' in header[:20]:
                is_video = True
            # Check for Matroska/WebM
            elif b'\x1a\x45\xdf\xa3' in header[:20]:
                is_video = True
        
        if not is_video:
            raise FileValidationError(
                "File does not appear to be a valid video file (magic byte check failed)"
            )
    
    @classmethod
    def _validate_with_opencv(cls, file_content: bytes, filename: str) -> None:
        """
        Ultimate validation: try to open with OpenCV
        This catches corrupted files, wrong formats, etc.
        """
        # Write to temporary file for OpenCV validation
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            # Try to open with OpenCV
            cap = cv2.VideoCapture(temp_path)
            
            if not cap.isOpened():
                raise FileValidationError("OpenCV cannot open this file - not a valid video")
            
            # Try to read basic properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Validate video properties
            if frame_count <= 0:
                raise FileValidationError("Video has no frames")
            
            if fps <= 0 or fps > 1000:  # Reasonable FPS range
                raise FileValidationError(f"Invalid FPS: {fps}")
            
            if width <= 0 or height <= 0:
                raise FileValidationError(f"Invalid dimensions: {width}x{height}")
            
            if width > 7680 or height > 4320:  # 8K max
                raise FileValidationError(
                    f"Video resolution too high: {width}x{height}. Max: 7680x4320"
                )
            
            # Try to read first frame to ensure it's not corrupted
            ret, frame = cap.read()
            if not ret or frame is None:
                raise FileValidationError("Cannot read video frames - file may be corrupted")
            
            cap.release()
            
        except cv2.error as e:
            raise FileValidationError(f"OpenCV validation failed: {str(e)}")
        except Exception as e:
            raise FileValidationError(f"Video validation failed: {str(e)}")
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass  # Ignore cleanup errors
    
    @classmethod
    def get_video_info(cls, file_content: bytes, filename: str) -> dict:
        """
        Get video information after validation
        Returns dict with video properties
        """
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            cap = cv2.VideoCapture(temp_path)
            
            info = {
                'filename': filename,
                'size_bytes': len(file_content),
                'size_mb': len(file_content) / (1024 * 1024),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration_seconds': 0,
                'codec': 'unknown'
            }
            
            # Calculate duration
            if info['fps'] > 0:
                info['duration_seconds'] = info['frame_count'] / info['fps']
            
            cap.release()
            return info
            
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
