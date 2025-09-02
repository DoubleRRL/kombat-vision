import React, { useState } from 'react';
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

export const TacticalDashboard: React.FC = () => {
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [totalFrames] = useState(8450);
  const [detectedTargets, setDetectedTargets] = useState(0);
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');
  const { toast } = useToast();

  const handleVideoUpload = (file: File) => {
    setUploadedVideo(file);
    const url = URL.createObjectURL(file);
    setVideoUrl(url);
    setStatus('idle');
    setProgress(0);
    setCurrentFrame(0);
    setDetectedTargets(0);
  };

  const handleStartProcessing = () => {
    if (!uploadedVideo) {
      toast({
        variant: "destructive",
        title: "No Video Loaded",
        description: "Please upload a video file first.",
      });
      return;
    }

    setIsProcessing(true);
    setStatus('processing');
    
    // Simulate processing
    let frame = 0;
    let targets = 0;
    const interval = setInterval(() => {
      frame += 25; // Simulate 25 FPS processing
      const progressPercent = (frame / totalFrames) * 100;
      
      // Randomly detect targets
      if (Math.random() > 0.95) {
        targets += 1;
        setDetectedTargets(targets);
      }
      
      setCurrentFrame(frame);
      setProgress(progressPercent);
      
      if (frame >= totalFrames) {
        clearInterval(interval);
        setIsProcessing(false);
        setStatus('completed');
        toast({
          title: "Processing Complete",
          description: `Detected ${targets} potential targets in video analysis.`,
        });
      }
    }, 100);
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
        className="relative h-32 bg-cover bg-center border-b border-tactical-green/30"
        style={{ backgroundImage: `url(${tacticalHero})` }}
      >
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />
        <div className="relative h-full flex items-center justify-between px-8">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-8 w-8 text-tactical-green" />
              <div>
                <h1 className="text-2xl font-bold text-foreground tracking-wider">
                  CV/SLAM TACTICAL ANALYSIS
                </h1>
                <p className="text-sm text-muted-foreground">
                  Enemy Detection & Surveillance Intelligence Platform
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
            <Badge variant="outline" className="text-tactical-green border-tactical-green/50">
              <Satellite className="h-3 w-3 mr-1" />
              OPERATIONAL
            </Badge>
            <Badge variant="outline" className="text-tactical-amber border-tactical-amber/50">
              <Radar className="h-3 w-3 mr-1" />
              SCANNING
            </Badge>
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <div className="container mx-auto p-6 space-y-6">
        {/* Upload Section */}
        {!uploadedVideo && (
          <div className="max-w-4xl mx-auto">
            <VideoUpload onVideoUpload={handleVideoUpload} />
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