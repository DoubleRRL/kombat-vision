"""
Working Thermal Detection System - Extracted from kombat-drone
Temperature-based detection that actually works on thermal images
"""
import cv2
import numpy as np
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class Detection:
    """Single target detection result"""
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str
    thermal_signature: Dict[str, float] = None


class WorkingThermalDetector:
    """
    Thermal detection system that actually works
    Uses temperature thresholding and contour analysis
    """
    
    def __init__(self, mode: str = "balanced"):
        self.mode = mode
        
        # Digital value thresholds for different threat types
        # NOTE: These are 8-bit digital values (0-255), NOT celsius temperatures!
        self.temp_thresholds = {
            "vehicle": {"min": 180, "max": 255, "min_area": 1000, "max_area": 15000},
            "personnel": {"min": 200, "max": 240, "min_area": 200, "max_area": 2000},
            "equipment": {"min": 160, "max": 200, "min_area": 500, "max_area": 8000},
            "aircraft": {"min": 190, "max": 255, "min_area": 2000, "max_area": 25000}
        }
        
        # Processing parameters based on mode
        if mode == "speed":
            self.blur_kernel = 3
            self.morph_kernel = 3
            self.min_confidence = 0.3
        elif mode == "balanced":
            self.blur_kernel = 5
            self.morph_kernel = 5
            self.min_confidence = 0.4
        else:  # accuracy
            self.blur_kernel = 7
            self.morph_kernel = 7
            self.min_confidence = 0.5
    
    def detect_thermal_targets(self, thermal_frame: np.ndarray) -> Tuple[List[Detection], Dict[str, float]]:
        """
        Detect thermal targets using temperature analysis
        """
        start_time = time.time()
        
        # Preprocess thermal image
        processed = self._preprocess_thermal(thermal_frame)
        
        # Find thermal hotspots
        hotspots = self._find_thermal_hotspots(processed)
        
        # Classify and validate targets
        detections = self._classify_thermal_targets(hotspots, thermal_frame)
        
        # Performance metrics
        processing_time = (time.time() - start_time) * 1000
        performance = {
            'fps': 1000 / processing_time if processing_time > 0 else 0,
            'inference_time_ms': processing_time,
            'detections_count': len(detections),
            'avg_confidence': np.mean([d.confidence for d in detections]) if detections else 0.0
        }
        
        return detections, performance
    
    def _preprocess_thermal(self, thermal_frame: np.ndarray) -> np.ndarray:
        """Preprocess thermal image for detection"""
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(thermal_frame, (self.blur_kernel, self.blur_kernel), 0)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(blurred)
        
        return enhanced
    
    def _find_thermal_hotspots(self, thermal_frame: np.ndarray) -> List[Dict[str, Any]]:
        """Find thermal hotspots using temperature thresholding"""
        hotspots = []
        
        # Multiple temperature ranges for different threat types
        temp_ranges = [
            (220, 255, "high_temp"),    # Very hot (engines, personnel)
            (180, 220, "medium_temp"),  # Warm (vehicles, equipment)
            (150, 180, "low_temp")      # Cool (structures, background objects)
        ]
        
        for min_temp, max_temp, temp_category in temp_ranges:
            # Create binary mask for this temperature range
            mask = cv2.inRange(thermal_frame, min_temp, max_temp)
            
            # Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                             (self.morph_kernel, self.morph_kernel))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Extract temperature statistics
                    roi = thermal_frame[y:y+h, x:x+w]
                    mean_temp = np.mean(roi)
                    max_temp_val = np.max(roi)
                    
                    hotspots.append({
                        'bbox': (x, y, x+w, y+h),
                        'area': area,
                        'mean_temp': mean_temp,
                        'max_temp': max_temp_val,
                        'temp_category': temp_category,
                        'aspect_ratio': w / h if h > 0 else 1.0
                    })
        
        return hotspots
    
    def _classify_thermal_targets(self, hotspots: List[Dict[str, Any]], thermal_frame: np.ndarray) -> List[Detection]:
        """Classify thermal hotspots into threat categories"""
        detections = []
        
        for hotspot in hotspots:
            area = hotspot['area']
            mean_temp = hotspot['mean_temp']
            max_temp = hotspot['max_temp']
            aspect_ratio = hotspot['aspect_ratio']
            bbox = hotspot['bbox']
            
            # Classification logic based on thermal digital values
            class_name = "unknown"
            confidence = 0.0
            
            # Vehicle detection (large, warm signature, rectangular)
            if (area >= 1000 and area <= 15000 and 
                mean_temp >= 180 and max_temp >= 200 and
                aspect_ratio > 1.2):
                class_name = "hostile_vehicle"
                confidence = min(0.9, 0.4 + (mean_temp - 180) / 100)
                
            # Personnel detection (medium size, body heat signature, vertical)
            elif (area >= 200 and area <= 2000 and
                  mean_temp >= 200 and max_temp >= 210 and
                  0.3 <= aspect_ratio <= 1.5):
                class_name = "hostile_personnel"
                confidence = min(0.9, 0.5 + (mean_temp - 200) / 50)
                
            # Aircraft detection (large, very hot engines)
            elif (area >= 2000 and area <= 25000 and
                  max_temp >= 230):
                class_name = "aircraft_threat"
                confidence = min(0.95, 0.6 + (max_temp - 230) / 25)
                
            # Equipment/infrastructure
            elif (area >= 500 and area <= 8000 and
                  mean_temp >= 160):
                class_name = "equipment"
                confidence = min(0.8, 0.3 + (mean_temp - 160) / 60)
                
            # Generic thermal signature
            elif area >= 150 and mean_temp >= 140:
                class_name = "thermal_signature"
                confidence = min(0.7, 0.2 + (mean_temp - 140) / 80)
            
            # Only add detections above confidence threshold
            if confidence >= self.min_confidence:
                detections.append(Detection(
                    bbox=bbox,
                    confidence=confidence,
                    class_id=self._get_class_id(class_name),
                    class_name=class_name,
                    thermal_signature={
                        'mean_temp': mean_temp,
                        'max_temp': max_temp,
                        'area': area
                    }
                ))
        
        # Sort by confidence and return top detections
        detections.sort(key=lambda x: x.confidence, reverse=True)
        return detections[:20]  # Limit to top 20 detections
    
    def _get_class_id(self, class_name: str) -> int:
        """Map class names to IDs"""
        class_map = {
            "hostile_personnel": 0,
            "hostile_vehicle": 1,
            "aircraft_threat": 2,
            "equipment": 3,
            "thermal_signature": 4
        }
        return class_map.get(class_name, 99)


def create_test_thermal_frame() -> np.ndarray:
    """Create a realistic thermal test frame for testing"""
    thermal_frame = np.ones((480, 640), dtype=np.uint8) * 85  # Background temp
    
    # Add realistic thermal signatures
    # Hot vehicle with engine
    cv2.rectangle(thermal_frame, (100, 200), (200, 260), 190, -1)  # Vehicle body
    cv2.rectangle(thermal_frame, (110, 210), (140, 230), 240, -1)  # Hot engine
    
    # Personnel with body heat
    cv2.ellipse(thermal_frame, (350, 250), (15, 35), 0, 0, 360, 215, -1)  # Body
    cv2.circle(thermal_frame, (350, 220), 8, 210, -1)  # Head
    
    # Aircraft with hot engines
    cv2.ellipse(thermal_frame, (500, 150), (60, 25), 0, 0, 360, 200, -1)  # Fuselage
    cv2.circle(thermal_frame, (480, 150), 12, 250, -1)  # Hot engine 1
    cv2.circle(thermal_frame, (520, 150), 12, 250, -1)  # Hot engine 2
    
    return thermal_frame
