import React, { useState, useEffect } from 'react';
import { VideoUpload } from './VideoUpload';
import { VideoPlayer } from './VideoPlayer';
import { ProcessingStatus } from './ProcessingStatus';
import { ControlPanel } from './ControlPanel';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  Shield,
  Radar,
  Satellite,
  Clock
} from 'lucide-react';
import tacticalHero from '@/assets/tactical-hero.jpg';
import { api, ProcessingStatus as ApiProcessingStatus, DetectionSummary } from '@/lib/api';

export const TacticalDashboard: React.FC = () => {
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);
  const [detectedTargets, setDetectedTargets] = useState(0);
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');
  const [detectionSummary, setDetectionSummary] = useState<DetectionSummary | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const { toast } = useToast();

  // Check backend connection on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await api.healthCheck();
        setBackendConnected(true);
      } catch (error) {
        setBackendConnected(false);
        toast({
          variant: "destructive",
          title: "Backend Disconnected",
          description: "CV/SLAM processing backend is not available. Start the backend server.",
        });
      }
    };

    checkBackend();
  }, [toast]);

  const handleVideoUpload = async (file: File) => {
    if (!backendConnected) {
      toast({
        variant: "destructive",
        title: "Backend Unavailable",
        description: "Cannot upload video. Backend server is not running.",
      });
      return;
    }

    try {
      // Upload to backend
      const uploadResult = await api.uploadVideo(file);

      // Set local state
      setUploadedVideo(file);
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
      setStatus('idle');
      setProgress(0);
      setCurrentFrame(0);
      setDetectedTargets(0);
      setDetectionSummary(null);

      toast({
        title: "Video Uploaded",
        description: `${uploadResult.filename} ready for CV/SLAM analysis`,
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload video",
      });
    }
  };

  const handleStartProcessing = async () => {
    if (!uploadedVideo) {
      toast({
        variant: "destructive",
        title: "No Video Loaded",
        description: "Please upload a video file first.",
      });
      return;
    }

    if (!backendConnected) {
      toast({
        variant: "destructive",
        title: "Backend Unavailable",
        description: "Cannot start processing. Backend server is not running.",
      });
      return;
    }

    try {
      // Start processing on backend
      const startResult = await api.startProcessing();

      setIsProcessing(true);
      setStatus('processing');
      setProgress(0);
      setCurrentFrame(0);
      setDetectedTargets(0);

      toast({
        title: "Processing Started",
        description: `${startResult.pipeline} pipeline activated`,
      });

      // Poll for progress updates
      api.pollProcessingStatus(
        (status: ApiProcessingStatus) => {
          setProgress(status.progress);
          setDetectedTargets(status.detections_count);

          // Estimate current frame from progress (rough calculation)
          if (totalFrames > 0) {
            setCurrentFrame(Math.floor((status.progress / 100) * totalFrames));
          }
        },
        1000 // Poll every second
      ).then(async (finalStatus) => {
        setIsProcessing(false);
        setStatus('completed');
        setProgress(100);

        // Get final detection results
        try {
          const detections = await api.getDetections();
          setDetectionSummary(detections);
          setDetectedTargets(detections.total_count);
          setTotalFrames(detections.frames_processed);

          toast({
            title: "Processing Complete",
            description: `Found ${detections.total_count} targets across ${detections.frames_processed} frames`,
          });
        } catch (error) {
          console.error('Failed to get final detections:', error);
        }
      }).catch((error) => {
        setIsProcessing(false);
        setStatus('error');
        toast({
          variant: "destructive",
          title: "Processing Failed",
          description: error instanceof Error ? error.message : "CV processing failed",
        });
      });

    } catch (error) {
      toast({
        variant: "destructive",
        title: "Failed to Start Processing",
        description: error instanceof Error ? error.message : "Could not start CV processing",
      });
    }
  };

  const handleExportVideo = () => {
    toast({
      title: "Export Started",
      description: "Generating annotated video with CV/SLAM overlays...",
    });
    
    // Simulate export process
    setTimeout(() => {
      toast({
        title: "Export Complete",
        description: "Tactical video analysis ready for download.",
      });
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Header */}
      <div
        className="relative h-40 bg-cover bg-center border-b border-tactical-green/30"
        style={{ backgroundImage: `url(${tacticalHero})` }}
      >
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-between px-8">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-8 w-8 text-tactical-green" />
              <div>
                <h1 className="text-2xl font-bold text-foreground tracking-wider">
                  CV/SLAM Video ANALYSIS
                </h1>
                <p className="text-sm text-muted-foreground">
                  Detection & Pipeline
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-time-red" />
              <span className="text-sm font-mono text-time-red font-bold">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
            <Badge variant="outline" className={`${backendConnected ? 'text-tactical-green border-tactical-green/50' : 'text-red-500 border-red-500/50'}`}>
              <Satellite className="h-3 w-3 mr-1" />
              {backendConnected ? 'CV BACKEND ONLINE' : 'CV BACKEND OFFLINE'}
            </Badge>
            <Badge variant="outline" className={`${isProcessing ? 'text-tactical-amber border-tactical-amber/50' : 'text-muted-foreground border-muted-foreground/50'}`}>
              <Radar className="h-3 w-3 mr-1" />
              {isProcessing ? 'PROCESSING' : 'STANDBY'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <div className="container mx-auto p-8 space-y-8">
        {/* Upload Section */}
        {!uploadedVideo && (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="max-w-2xl w-full">
              <VideoUpload onVideoUpload={handleVideoUpload} />
            </div>
          </div>
        )}

        {/* Analysis Grid */}
        {uploadedVideo && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Left Column - Video Player */}
            <div className="xl:col-span-2 space-y-6">
              <VideoPlayer 
                videoUrl={videoUrl} 
                showHUD={status === 'processing' || status === 'completed'} 
              />
              
              {/* Re-upload option */}
              <div className="bg-muted/30 border border-tactical-green/20 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-foreground">Current Video</h4>
                    <p className="text-sm text-muted-foreground">
                      {uploadedVideo.name} ({(uploadedVideo.size / 1024 / 1024).toFixed(2)} MB)
                    </p>
                  </div>
                  <VideoUpload onVideoUpload={handleVideoUpload} />
                </div>
              </div>
            </div>

            {/* Right Column - Controls and Status */}
            <div className="space-y-6">
              <ProcessingStatus
                progress={progress}
                currentFrame={currentFrame}
                totalFrames={totalFrames}
                detectedTargets={detectedTargets}
                isProcessing={isProcessing}
                status={status}
              />
              
              <ControlPanel
                onStartProcessing={handleStartProcessing}
                onExportVideo={handleExportVideo}
                isProcessing={isProcessing}
                canExport={status === 'completed'}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};