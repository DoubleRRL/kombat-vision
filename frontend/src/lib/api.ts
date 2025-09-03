/**
 * API service for CV/SLAM backend communication
 * Connects frontend to real thermal detection pipeline
 */

const API_BASE_URL = 'http://localhost:8000';

export interface DetectionResult {
  bbox: [number, number, number, number];
  confidence: number;
  class_id: number;
  class_name: string;
  thermal_signature?: {
    mean_temp: number;
    max_temp: number;
    area: number;
  };
}

export interface FrameDetection {
  frame_number: number;
  timestamp: number;
  detections: DetectionResult[];
  count: number;
}

export interface ProcessingStatus {
  is_processing: boolean;
  progress: number;
  current_video: {
    filename: string;
    path: string;
    size: number;
    uploaded_at: number;
  } | null;
  detections_count: number;
  slam_status: string;
}

export interface DetectionSummary {
  detections: FrameDetection[];
  total_count: number;
  frames_processed: number;
  video: string | null;
  summary: Record<string, { count: number; max_confidence: number }>;
  performance: {
    total_detections: number;
    avg_fps: number;
    avg_confidence: number;
    processing_time_ms: number;
    frames_processed: number;
    video_duration_sec: number;
  };
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new ApiError(response.status, errorText || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export const api = {
  /**
   * Check if backend is operational
   */
  async healthCheck(): Promise<{ message: string; status: string }> {
    return apiRequest('/');
  },

  /**
   * Upload video file for processing
   */
  async uploadVideo(file: File): Promise<{
    message: string;
    filename: string;
    size: number;
    status: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload-video`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new ApiError(response.status, errorText || `Upload failed: HTTP ${response.status}`);
    }

    return await response.json();
  },

  /**
   * Start CV/SLAM processing on uploaded video
   */
  async startProcessing(): Promise<{
    message: string;
    video: string;
    status: string;
    pipeline: string;
  }> {
    return apiRequest('/start-processing', {
      method: 'POST',
    });
  },

  /**
   * Get current processing status
   */
  async getProcessingStatus(): Promise<ProcessingStatus> {
    return apiRequest('/processing-status');
  },

  /**
   * Get detection results
   */
  async getDetections(): Promise<DetectionSummary> {
    return apiRequest('/detections');
  },

  /**
   * Get detections for specific frame
   */
  async getFrameDetections(frameNumber: number): Promise<FrameDetection> {
    return apiRequest(`/detections/frame/${frameNumber}`);
  },

  /**
   * Poll processing status until completion
   */
  async pollProcessingStatus(
    onProgress: (status: ProcessingStatus) => void,
    intervalMs: number = 1000
  ): Promise<ProcessingStatus> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getProcessingStatus();
          onProgress(status);

          if (!status.is_processing) {
            resolve(status);
          } else {
            setTimeout(poll, intervalMs);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },
};

/**
 * Format thermal temperature from digital value to approximate celsius
 * Digital values 0-255 map roughly to real temperatures
 */
export function formatThermalTemp(digitalValue: number): string {
  // Rough mapping: 0-255 digital -> -10 to 80°C actual
  const celsius = ((digitalValue / 255) * 90) - 10;
  return `${celsius.toFixed(1)}°C`;
}

/**
 * Get threat level based on detection class
 */
export function getThreatLevel(className: string): 'high' | 'medium' | 'low' {
  const highThreat = ['hostile_personnel', 'hostile_vehicle', 'aircraft_threat'];
  const mediumThreat = ['equipment'];
  
  if (highThreat.includes(className)) return 'high';
  if (mediumThreat.includes(className)) return 'medium';
  return 'low';
}

/**
 * Format detection class name for display
 */
export function formatClassName(className: string): string {
  return className
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
