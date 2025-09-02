import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { 
  Settings, 
  Download, 
  Play, 
  Target, 
  Map, 
  Eye,
  Shield,
  Zap
} from 'lucide-react';

interface ControlPanelProps {
  onStartProcessing: () => void;
  onExportVideo: () => void;
  isProcessing: boolean;
  canExport: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  onStartProcessing,
  onExportVideo,
  isProcessing,
  canExport
}) => {
  const [confidence, setConfidence] = React.useState([0.75]);
  const [enableSLAM, setEnableSLAM] = React.useState(true);
  const [showHUD, setShowHUD] = React.useState(true);
  const [frameSkip, setFrameSkip] = React.useState([1]);

  return (
    <Card className="bg-card border-tactical-green/30">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-3">
          <Settings className="h-5 w-5 text-tactical-green" />
          <h3 className="text-lg font-bold text-foreground">MISSION CONTROL</h3>
          <Badge variant="outline" className="text-tactical-green border-tactical-green/50">
            OPERATIONAL
          </Badge>
        </div>

        <Separator className="bg-tactical-green/20" />

        {/* CV Pipeline Settings */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Target className="h-4 w-4 text-tactical-red" />
            <h4 className="font-semibold text-foreground">Detection Parameters</h4>
          </div>
          
          <div className="space-y-4 pl-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label htmlFor="confidence" className="text-sm">Confidence Threshold</Label>
                <span className="text-sm font-mono text-tactical-green">
                  {(confidence[0] * 100).toFixed(0)}%
                </span>
              </div>
              <Slider
                id="confidence"
                value={confidence}
                onValueChange={setConfidence}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label htmlFor="frameskip" className="text-sm">Frame Skip</Label>
                <span className="text-sm font-mono text-tactical-blue">
                  {frameSkip[0]}
                </span>
              </div>
              <Slider
                id="frameskip"
                value={frameSkip}
                onValueChange={setFrameSkip}
                min={1}
                max={10}
                step={1}
                className="w-full"
              />
            </div>
          </div>
        </div>

        <Separator className="bg-tactical-green/20" />

        {/* SLAM Settings */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Map className="h-4 w-4 text-tactical-green" />
            <h4 className="font-semibold text-foreground">SLAM Configuration</h4>
          </div>
          
          <div className="flex items-center justify-between pl-6">
            <Label htmlFor="slam-toggle" className="text-sm">Enable SLAM Tracking</Label>
            <Switch
              id="slam-toggle"
              checked={enableSLAM}
              onCheckedChange={setEnableSLAM}
            />
          </div>
        </div>

        <Separator className="bg-tactical-green/20" />

        {/* HUD Settings */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Eye className="h-4 w-4 text-tactical-amber" />
            <h4 className="font-semibold text-foreground">HUD Display</h4>
          </div>
          
          <div className="flex items-center justify-between pl-6">
            <Label htmlFor="hud-toggle" className="text-sm">Show Military HUD</Label>
            <Switch
              id="hud-toggle"
              checked={showHUD}
              onCheckedChange={setShowHUD}
            />
          </div>
        </div>

        <Separator className="bg-tactical-green/20" />

        {/* Action Buttons */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Shield className="h-4 w-4 text-tactical-blue" />
            <h4 className="font-semibold text-foreground">Mission Actions</h4>
          </div>

          <div className="grid grid-cols-1 gap-3">
            <Button
              variant="tactical"
              size="lg"
              onClick={onStartProcessing}
              disabled={isProcessing}
              className="w-full"
            >
              {isProcessing ? (
                <>
                  <Zap className="h-4 w-4 animate-pulse" />
                  PROCESSING...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  INITIATE CV/SLAM ANALYSIS
                </>
              )}
            </Button>

            <Button
              variant="command"
              size="lg"
              onClick={onExportVideo}
              disabled={!canExport}
              className="w-full"
            >
              <Download className="h-4 w-4" />
              EXPORT ANNOTATED VIDEO
            </Button>
          </div>

          {!canExport && (
            <div className="text-xs text-muted-foreground text-center">
              Complete processing to enable export
            </div>
          )}
        </div>

        {/* System Status */}
        <div className="bg-tactical-green/10 border border-tactical-green/30 rounded-lg p-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">CV Pipeline</span>
              <Badge variant="outline" className="text-tactical-green border-tactical-green/50">
                READY
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">SLAM System</span>
              <Badge variant="outline" className={`${enableSLAM ? 'text-tactical-green border-tactical-green/50' : 'text-muted-foreground border-muted'}`}>
                {enableSLAM ? 'ACTIVE' : 'DISABLED'}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">HUD Overlay</span>
              <Badge variant="outline" className={`${showHUD ? 'text-tactical-amber border-tactical-amber/50' : 'text-muted-foreground border-muted'}`}>
                {showHUD ? 'ENABLED' : 'DISABLED'}
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};