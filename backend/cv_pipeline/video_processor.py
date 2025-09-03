"""
Video Processing Pipeline with CV/SLAM Integration
Handles video files and applies thermal detection frame by frame
"""
import cv2
import numpy as np
import time
import asyncio
import gc
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json
from dataclasses import asdict

from .thermal_detector import WorkingThermalDetector, Detection, create_test_thermal_frame


class VideoProcessor:
    """
    Process video files with CV/SLAM pipeline
    Includes error recovery, memory management, and progress persistence
    """

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.thermal_detector = WorkingThermalDetector(mode="balanced")
        self.progress_callback = progress_callback
        self.is_processing = False
        self.should_stop = False

        # Processing state
        self.current_frame = 0
        self.total_frames = 0
        self.detections_history = []
        self.performance_metrics = {
            'total_detections': 0,
            'avg_fps': 0.0,
            'avg_confidence': 0.0,
            'processing_time_ms': 0.0
        }

        # Error recovery and memory management
        self.max_memory_mb = 2048  # 2GB memory limit
        self.checkpoint_interval = 100  # Save progress every 100 frames
        self.max_consecutive_errors = 5
        self.error_count = 0
        self.last_checkpoint_frame = 0
    
    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        Process video file with thermal detection
        Returns processing results and metrics
        """
        if self.is_processing:
            raise ValueError("Already processing a video")
        
        self.is_processing = True
        self.should_stop = False
        self.detections_history = []
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            # Get video properties
            self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"Processing video: {width}x{height}, {self.total_frames} frames, {fps:.1f} FPS")
            
            # Processing metrics
            start_time = time.time()
            frame_times = []
            all_detections = []
            
            self.current_frame = 0
            
            while True:
                if self.should_stop:
                    break

                try:
                    # Memory management check
                    if self.current_frame % 50 == 0:  # Check every 50 frames
                        memory_usage = self._check_memory_usage()
                        if memory_usage > self.max_memory_mb:
                            print(f"Memory limit exceeded: {memory_usage}MB > {self.max_memory_mb}MB")
                            self._cleanup_memory()

                    ret, frame = cap.read()
                    if not ret:
                        break

                    frame_start = time.time()

                    # Convert to thermal-like representation for testing
                    # In production, this would be actual thermal data
                    thermal_frame = self._simulate_thermal_from_rgb(frame)

                    # Apply thermal detection with error handling
                    try:
                        detections, frame_performance = self.thermal_detector.detect_thermal_targets(thermal_frame)
                        self.error_count = 0  # Reset error count on success
                    except Exception as e:
                        print(f"Detection error on frame {self.current_frame}: {e}")
                        self.error_count += 1

                        if self.error_count >= self.max_consecutive_errors:
                            raise Exception(f"Too many consecutive errors ({self.error_count}). Stopping processing.")

                        # Use empty detections for failed frame
                        detections = []
                        frame_performance = {'fps': 0, 'inference_time_ms': 0, 'detections_count': 0, 'avg_confidence': 0}

                    # Store frame results
                    frame_result = {
                        'frame_number': self.current_frame,
                        'timestamp': self.current_frame / fps if fps > 0 else 0,
                        'detections': [asdict(d) for d in detections],
                        'performance': frame_performance,
                        'error_count': self.error_count
                    }

                    self.detections_history.append(frame_result)
                    all_detections.extend(detections)

                    # Track timing
                    frame_time = time.time() - frame_start
                    frame_times.append(frame_time)

                    self.current_frame += 1

                    # Progress persistence - save checkpoint
                    if self.current_frame % self.checkpoint_interval == 0:
                        self._save_checkpoint(video_path, self.current_frame)

                    # Update progress
                    progress = (self.current_frame / self.total_frames) * 100
                    if self.progress_callback:
                        await self.progress_callback({
                            'progress': progress,
                            'current_frame': self.current_frame,
                            'total_frames': self.total_frames,
                            'detections_count': len(all_detections),
                            'current_fps': frame_performance.get('fps', 0),
                            'memory_usage_mb': self._check_memory_usage(),
                            'error_count': self.error_count
                        })

                    # Yield control to allow other operations
                    if self.current_frame % 10 == 0:
                        await asyncio.sleep(0.001)

                except Exception as frame_error:
                    print(f"Critical error processing frame {self.current_frame}: {frame_error}")
                    self.error_count += 1

                    if self.error_count >= self.max_consecutive_errors:
                        raise Exception(f"Critical processing failure: {frame_error}")

                    # Skip this frame and continue
                    self.current_frame += 1
                    continue
            
            cap.release()
            
            # Calculate final metrics
            total_time = time.time() - start_time
            avg_frame_time = np.mean(frame_times) if frame_times else 0
            
            self.performance_metrics = {
                'total_detections': len(all_detections),
                'avg_fps': 1.0 / avg_frame_time if avg_frame_time > 0 else 0,
                'avg_confidence': np.mean([d.confidence for d in all_detections]) if all_detections else 0.0,
                'processing_time_ms': total_time * 1000,
                'frames_processed': self.current_frame,
                'video_duration_sec': self.current_frame / fps if fps > 0 else 0
            }
            
            return {
                'status': 'completed',
                'metrics': self.performance_metrics,
                'detections_summary': self._summarize_detections(all_detections),
                'frame_count': self.current_frame
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'frames_processed': self.current_frame
            }
        finally:
            self.is_processing = False
    
    def _simulate_thermal_from_rgb(self, rgb_frame: np.ndarray) -> np.ndarray:
        """
        Convert RGB frame to thermal-like representation for testing
        In production, this would be replaced with actual thermal camera data
        """
        # Convert to grayscale
        gray = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2GRAY)
        
        # Simulate thermal characteristics
        # Bright areas = hot, dark areas = cold
        thermal_sim = gray.copy()
        
        # Add some thermal noise and characteristics
        thermal_sim = cv2.GaussianBlur(thermal_sim, (3, 3), 0)
        
        # Enhance contrast to simulate thermal imaging
        thermal_sim = cv2.equalizeHist(thermal_sim)
        
        # Add some random hot spots to simulate thermal signatures
        if np.random.random() > 0.7:  # 30% chance of adding thermal signatures
            h, w = thermal_sim.shape
            # Add random hot spots
            for _ in range(np.random.randint(1, 4)):
                x = np.random.randint(50, w-50)
                y = np.random.randint(50, h-50)
                size = np.random.randint(10, 30)
                intensity = np.random.randint(200, 255)
                cv2.circle(thermal_sim, (x, y), size, intensity, -1)
        
        return thermal_sim
    
    def _summarize_detections(self, detections: List[Detection]) -> Dict[str, Any]:
        """Summarize detection results"""
        if not detections:
            return {'total': 0, 'by_class': {}}
        
        by_class = {}
        for detection in detections:
            class_name = detection.class_name
            if class_name not in by_class:
                by_class[class_name] = {
                    'count': 0,
                    'avg_confidence': 0.0,
                    'max_confidence': 0.0
                }
            
            by_class[class_name]['count'] += 1
            by_class[class_name]['max_confidence'] = max(
                by_class[class_name]['max_confidence'], 
                detection.confidence
            )
        
        # Calculate average confidences
        for class_name in by_class:
            class_detections = [d for d in detections if d.class_name == class_name]
            by_class[class_name]['avg_confidence'] = np.mean([d.confidence for d in class_detections])
        
        return {
            'total': len(detections),
            'by_class': by_class,
            'highest_confidence': max(d.confidence for d in detections),
            'avg_confidence': np.mean([d.confidence for d in detections])
        }
    
    def stop_processing(self):
        """Stop current processing"""
        self.should_stop = True
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        return {
            'is_processing': self.is_processing,
            'current_frame': self.current_frame,
            'total_frames': self.total_frames,
            'progress': (self.current_frame / self.total_frames * 100) if self.total_frames > 0 else 0,
            'detections_count': len(self.detections_history),
            'performance': self.performance_metrics
        }
    
    def get_detections_for_frame(self, frame_number: int) -> Optional[Dict[str, Any]]:
        """Get detections for a specific frame"""
        for frame_data in self.detections_history:
            if frame_data['frame_number'] == frame_number:
                return frame_data
        return None
    
    def get_all_detections(self) -> List[Dict[str, Any]]:
        """Get all detection results"""
        return self.detections_history

    def _check_memory_usage(self) -> float:
        """Check current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except:
            return 0.0

    def _cleanup_memory(self):
        """Force garbage collection and memory cleanup"""
        print("Performing memory cleanup...")

        # Limit detection history to last 1000 frames to save memory
        if len(self.detections_history) > 1000:
            self.detections_history = self.detections_history[-1000:]
            print(f"Trimmed detection history to last 1000 frames")

        # Force garbage collection
        gc.collect()

        print(f"Memory usage after cleanup: {self._check_memory_usage():.1f}MB")

    def _save_checkpoint(self, video_path: str, frame_number: int):
        """Save processing checkpoint for recovery"""
        try:
            checkpoint_data = {
                'video_path': video_path,
                'frame_number': frame_number,
                'total_frames': self.total_frames,
                'detections_count': len([d for frame in self.detections_history for d in frame["detections"]]),
                'timestamp': time.time(),
                'performance_metrics': self.performance_metrics
            }

            checkpoint_file = f"backend/checkpoints/checkpoint_{int(time.time())}.json"
            os.makedirs("backend/checkpoints", exist_ok=True)

            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            # Keep only last 5 checkpoints
            self._cleanup_old_checkpoints()

            self.last_checkpoint_frame = frame_number
            print(f"Checkpoint saved at frame {frame_number}")

        except Exception as e:
            print(f"Failed to save checkpoint: {e}")

    def _cleanup_old_checkpoints(self):
        """Keep only the most recent checkpoints"""
        try:
            checkpoint_dir = "backend/checkpoints"
            if not os.path.exists(checkpoint_dir):
                return

            checkpoints = [f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint_')]
            checkpoints.sort(key=lambda x: os.path.getctime(os.path.join(checkpoint_dir, x)), reverse=True)

            # Keep only last 5 checkpoints
            for old_checkpoint in checkpoints[5:]:
                try:
                    os.remove(os.path.join(checkpoint_dir, old_checkpoint))
                except:
                    pass
        except Exception as e:
            print(f"Failed to cleanup old checkpoints: {e}")

    def can_resume_processing(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Check if processing can be resumed from a checkpoint"""
        try:
            checkpoint_dir = "backend/checkpoints"
            if not os.path.exists(checkpoint_dir):
                return None

            checkpoints = [f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint_')]
            if not checkpoints:
                return None

            # Get most recent checkpoint
            latest_checkpoint = max(checkpoints,
                                  key=lambda x: os.path.getctime(os.path.join(checkpoint_dir, x)))

            with open(os.path.join(checkpoint_dir, latest_checkpoint), 'r') as f:
                checkpoint_data = json.load(f)

            # Check if checkpoint is for the same video
            if checkpoint_data.get('video_path') == video_path:
                return checkpoint_data

            return None

        except Exception as e:
            print(f"Failed to check for resume capability: {e}")
            return None


async def test_video_processor():
    """Test the video processor with a synthetic thermal frame"""
    print("Testing video processor...")
    
    # Create test thermal frame
    test_frame = create_test_thermal_frame()
    
    # Test thermal detection
    detector = WorkingThermalDetector()
    detections, performance = detector.detect_thermal_targets(test_frame)
    
    print(f"Test detection results:")
    print(f"- Found {len(detections)} targets")
    print(f"- Processing FPS: {performance['fps']:.1f}")
    print(f"- Average confidence: {performance['avg_confidence']:.2f}")
    
    for i, detection in enumerate(detections):
        print(f"  {i+1}. {detection.class_name}: {detection.confidence:.2f}")
    
    return len(detections) > 0
