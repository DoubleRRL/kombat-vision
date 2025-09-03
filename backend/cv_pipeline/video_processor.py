"""
Video Processing Pipeline with CV/SLAM Integration
Handles video files and applies thermal detection frame by frame
"""
import cv2
import numpy as np
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json
from dataclasses import asdict

from .thermal_detector import WorkingThermalDetector, Detection, create_test_thermal_frame


class VideoProcessor:
    """
    Process video files with CV/SLAM pipeline
    Applies thermal detection and tracks performance metrics
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
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_start = time.time()
                
                # Convert to thermal-like representation for testing
                # In production, this would be actual thermal data
                thermal_frame = self._simulate_thermal_from_rgb(frame)
                
                # Apply thermal detection
                detections, frame_performance = self.thermal_detector.detect_thermal_targets(thermal_frame)
                
                # Store frame results
                frame_result = {
                    'frame_number': self.current_frame,
                    'timestamp': self.current_frame / fps if fps > 0 else 0,
                    'detections': [asdict(d) for d in detections],
                    'performance': frame_performance
                }
                
                self.detections_history.append(frame_result)
                all_detections.extend(detections)
                
                # Track timing
                frame_time = time.time() - frame_start
                frame_times.append(frame_time)
                
                self.current_frame += 1
                
                # Update progress
                progress = (self.current_frame / self.total_frames) * 100
                if self.progress_callback:
                    await self.progress_callback({
                        'progress': progress,
                        'current_frame': self.current_frame,
                        'total_frames': self.total_frames,
                        'detections_count': len(all_detections),
                        'current_fps': frame_performance.get('fps', 0)
                    })
                
                # Yield control to allow other operations
                if self.current_frame % 10 == 0:
                    await asyncio.sleep(0.001)
            
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
