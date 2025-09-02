import React from 'react';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  Eye, 
  Target, 
  Map, 
  Activity,
  CheckCircle,
  AlertCircle 
} from 'lucide-react';

interface ProcessingStatusProps {
  progress: number;
  currentFrame: number;
  totalFrames: number;
  detectedTargets: number;
  isProcessing: boolean;
  status: 'idle' | 'processing' | 'completed' | 'error';
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  progress,
  currentFrame,
  totalFrames,
  detectedTargets,
  isProcessing,
  status
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'processing': return 'text-tactical-blue';
      case 'completed': return 'text-tactical-green';
      case 'error': return 'text-tactical-red';
      default: return 'text-muted-foreground';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'processing': return <Activity className="h-5 w-5 animate-pulse" />;
      case 'completed': return <CheckCircle className="h-5 w-5" />;
      case 'error': return <AlertCircle className="h-5 w-5" />;
      default: return <Eye className="h-5 w-5" />;
    }
  };

  return (
    <Card className="bg-card border-tactical-green/30 p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <h3 className={`text-lg font-bold ${getStatusColor()}`}>
              CV/SLAM PIPELINE STATUS
            </h3>
          </div>
          {isProcessing ? (
            <Pause className="h-5 w-5 text-tactical-amber" />
          ) : (
            <Play className="h-5 w-5 text-tactical-green" />
          )}
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Processing Progress</span>
            <span className="text-tactical-green font-mono">{progress.toFixed(1)}%</span>
          </div>
          <Progress 
            value={progress} 
            className="h-3 bg-muted"
          />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-muted/30 rounded-lg p-4 border border-tactical-green/20">
            <div className="flex items-center space-x-2 mb-2">
              <Play className="h-4 w-4 text-tactical-blue" />
              <span className="text-sm text-muted-foreground">Frame</span>
            </div>
            <div className="font-mono text-lg font-bold text-foreground">
              {currentFrame.toLocaleString()} / {totalFrames.toLocaleString()}
            </div>
          </div>

          <div className="bg-muted/30 rounded-lg p-4 border border-tactical-red/20">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-4 w-4 text-tactical-red" />
              <span className="text-sm text-muted-foreground">Targets</span>
            </div>
            <div className="font-mono text-lg font-bold text-tactical-red">
              {detectedTargets}
            </div>
          </div>

          <div className="bg-muted/30 rounded-lg p-4 border border-tactical-green/20">
            <div className="flex items-center space-x-2 mb-2">
              <Map className="h-4 w-4 text-tactical-green" />
              <span className="text-sm text-muted-foreground">SLAM</span>
            </div>
            <Badge variant="outline" className="text-tactical-green border-tactical-green/50">
              ACTIVE
            </Badge>
          </div>

          <div className="bg-muted/30 rounded-lg p-4 border border-tactical-amber/20">
            <div className="flex items-center space-x-2 mb-2">
              <Eye className="h-4 w-4 text-tactical-amber" />
              <span className="text-sm text-muted-foreground">Vision</span>
            </div>
            <Badge variant="outline" className="text-tactical-amber border-tactical-amber/50">
              ONLINE
            </Badge>
          </div>
        </div>

        {/* Status Message */}
        <div className="bg-tactical-green/10 border border-tactical-green/30 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-tactical-green rounded-full animate-pulse" />
            <span className="text-sm font-medium text-tactical-green">
              {status === 'processing' && 'Analyzing frames for enemy detection...'}
              {status === 'completed' && 'Processing complete. Video ready for export.'}
              {status === 'error' && 'Processing error. Check video format and try again.'}
              {status === 'idle' && 'Awaiting video upload to begin analysis.'}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};