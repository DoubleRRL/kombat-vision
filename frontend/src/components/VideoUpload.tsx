import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Upload, FileVideo, AlertTriangle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface VideoUploadProps {
  onVideoUpload: (file: File) => void;
}

export const VideoUpload: React.FC<VideoUploadProps> = ({ onVideoUpload }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const { toast } = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (file.type.startsWith('video/')) {
        onVideoUpload(file);
        toast({
          title: "Video Uploaded",
          description: `${file.name} ready for processing`,
        });
      } else {
        toast({
          variant: "destructive",
          title: "Invalid File Type",
          description: "Please upload a video file (MP4, AVI, MOV, etc.)",
        });
      }
    }
  }, [onVideoUpload, toast]);

  const { getRootProps, getInputProps, isDragActive: dropzoneActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
    },
    multiple: false,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
  });

  return (
    <Card className="tactical-upload-zone border-green-400/30 bg-card hover:border-green-400/50 transition-all duration-300">
      <div
        {...getRootProps()}
        className={`
          p-12 text-center cursor-pointer rounded-lg transition-all duration-300
          ${isDragActive || dropzoneActive 
            ? 'bg-green-400/10 border-2 border-dashed border-green-400' 
            : 'border-2 border-dashed border-muted hover:border-green-400/50'
          }
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {isDragActive || dropzoneActive ? (
            <Upload className="h-16 w-16 text-green-400 animate-pulse" />
          ) : (
            <FileVideo className="h-16 w-16 text-muted-foreground" />
          )}
          
          <div className="space-y-2">
            <h3 className="text-xl font-bold text-foreground">
              {isDragActive ? 'Drop video here' : 'Upload Target Video'}
            </h3>
            <p className="text-muted-foreground">
              Drag & drop your building walkthrough video or click to browse
            </p>
            <div className="flex items-center justify-center space-x-2 text-sm text-amber-400">
              <AlertTriangle className="h-4 w-4" />
              <span>Supported: MP4, AVI, MOV, MKV, WebM, FLV</span>
            </div>
          </div>
          
          <Button variant="tactical" size="lg" className="font-sans font-bold">
            SELECT VIDEO FILE
          </Button>
        </div>
      </div>
    </Card>
  );
};