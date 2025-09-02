import React, { useRef, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  Volume2, 
  Maximize,
  Eye,
  Target
} from 'lucide-react';

interface VideoPlayerProps {
  videoUrl?: string;
  showHUD?: boolean;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  videoUrl, 
  showHUD = false 
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeek = (values: number[]) => {
    if (videoRef.current) {
      videoRef.current.currentTime = values[0];
      setCurrentTime(values[0]);
    }
  };

  const handleVolumeChange = (values: number[]) => {
    const newVolume = values[0];
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="bg-card border-tactical-green/30 overflow-hidden">
      <div className="relative">
        {/* Video Element */}
        <div className="relative bg-black aspect-video">
          {videoUrl ? (
            <video
              ref={videoRef}
              className="w-full h-full object-contain"
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onEnded={() => setIsPlaying(false)}
            >
              <source src={videoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center space-y-4">
                <Eye className="h-16 w-16 mx-auto opacity-50" />
                <p className="text-lg">No video loaded</p>
                <p className="text-sm">Upload a video to begin analysis</p>
              </div>
            </div>
          )}

          {/* HUD Overlay */}
          {showHUD && videoUrl && (
            <div className="absolute inset-0 pointer-events-none">
              {/* Top HUD Bar */}
              <div className="absolute top-4 left-4 right-4 flex justify-between items-start">
                <div className="bg-background/90 border border-tactical-green/50 rounded px-3 py-2">
                  <div className="flex items-center space-x-2 text-sm">
                    <Target className="h-4 w-4 text-tactical-red" />
                    <span className="text-tactical-red font-mono font-bold">3 TARGETS</span>
                  </div>
                </div>
                <div className="bg-background/90 border border-tactical-green/50 rounded px-3 py-2">
                  <div className="text-sm text-tactical-green font-mono">
                    STATUS: TRACKING
                  </div>
                </div>
              </div>

              {/* Crosshairs */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="relative">
                  <div className="w-8 h-8 border-2 border-tactical-green/70 rounded-full"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-1 h-1 bg-tactical-green rounded-full"></div>
                  </div>
                </div>
              </div>

              {/* Target Detection Boxes - More Dynamic */}
              <div className="absolute top-1/4 left-1/3 w-20 h-24 border-2 border-tactical-red rounded animate-pulse">
                <div className="absolute -top-6 left-0 bg-tactical-red/90 text-background text-xs px-2 py-1 rounded font-military">
                  HOSTILE
                </div>
                <div className="absolute bottom-0 left-0 bg-tactical-red/70 text-background text-xs px-1 py-0.5 rounded-br font-mono">
                  87%
                </div>
              </div>
              <div className="absolute top-1/2 right-1/4 w-16 h-20 border-2 border-tactical-red rounded animate-pulse">
                <div className="absolute -top-6 left-0 bg-tactical-red/90 text-background text-xs px-2 py-1 rounded font-military">
                  PERSON
                </div>
                <div className="absolute bottom-0 left-0 bg-tactical-red/70 text-background text-xs px-1 py-0.5 rounded-br font-mono">
                  94%
                </div>
              </div>
              <div className="absolute bottom-1/3 left-1/4 w-18 h-22 border-2 border-tactical-amber rounded animate-pulse">
                <div className="absolute -top-6 left-0 bg-tactical-amber/90 text-background text-xs px-2 py-1 rounded font-military">
                  UNKNOWN
                </div>
                <div className="absolute bottom-0 left-0 bg-tactical-amber/70 text-background text-xs px-1 py-0.5 rounded-br font-mono">
                  72%
                </div>
              </div>

              {/* SLAM Trajectory and Movement Path */}
              <svg className="absolute inset-0 w-full h-full">
                <path
                  d="M 50 300 Q 150 250 250 280 T 450 260"
                  stroke="hsl(var(--friendly-green))"
                  strokeWidth="2"
                  fill="none"
                  strokeDasharray="8,4"
                  className="animate-pulse opacity-80"
                />
                <circle cx="450" cy="260" r="4" fill="hsl(var(--friendly-green))" className="animate-ping" />
                <text x="460" y="265" className="text-xs fill-current text-tactical-green font-military">POSITION</text>
              </svg>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="p-4 space-y-4 bg-card border-t border-tactical-green/30">
          {/* Progress Bar */}
          <div className="space-y-2">
            <Slider
              value={[currentTime]}
              max={duration || 100}
              step={0.1}
              onValueChange={handleSeek}
              className="w-full"
              disabled={!videoUrl}
            />
            <div className="flex justify-between text-sm text-muted-foreground font-mono">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => {
                  if (videoRef.current) {
                    videoRef.current.currentTime = Math.max(0, currentTime - 10);
                  }
                }}
                disabled={!videoUrl}
              >
                <SkipBack className="h-4 w-4" />
              </Button>
              
              <Button
                variant="tactical"
                size="icon"
                onClick={togglePlay}
                disabled={!videoUrl}
              >
                {isPlaying ? (
                  <Pause className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
              </Button>
              
              <Button
                variant="outline"
                size="icon"
                onClick={() => {
                  if (videoRef.current) {
                    videoRef.current.currentTime = Math.min(duration, currentTime + 10);
                  }
                }}
                disabled={!videoUrl}
              >
                <SkipForward className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex items-center space-x-4">
              {/* Volume Control */}
              <div className="flex items-center space-x-2">
                <Volume2 className="h-4 w-4 text-muted-foreground" />
                <Slider
                  value={[volume]}
                  max={1}
                  step={0.1}
                  onValueChange={handleVolumeChange}
                  className="w-20"
                />
              </div>

              <Button variant="outline" size="icon" disabled={!videoUrl}>
                <Maximize className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};