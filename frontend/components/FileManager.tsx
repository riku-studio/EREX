import React, { useState, useRef } from 'react';
import { UploadCloud, File as FileIcon, Trash2, CheckCircle2, AlertCircle, HardDrive } from 'lucide-react';
import { Button } from './Button';
import { UploadResponseItem } from '../types';

interface FileManagerProps {
  files: UploadResponseItem[];
  isUploading: boolean;
  onUpload: (files: File[]) => void;
  onDelete: (filenames: string[]) => void;
}

export const FileManager: React.FC<FileManagerProps> = ({ files, isUploading, onUpload, onDelete }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      onUpload(Array.from(e.target.files));
    }
  };

  const toggleSelect = (filename: string) => {
    const next = new Set(selectedFiles);
    if (next.has(filename)) {
      next.delete(filename);
    } else {
      next.add(filename);
    }
    setSelectedFiles(next);
  };

  const handleDeleteSelected = () => {
    if (confirm(`Delete ${selectedFiles.size} files?`)) {
      onDelete(Array.from(selectedFiles));
      setSelectedFiles(new Set());
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-slate-500" />
            File Management
          </h2>
          <p className="text-slate-500 text-sm mt-1">Upload .pst, .eml, or .msg files for processing.</p>
        </div>
        {selectedFiles.size > 0 && (
          <Button 
            variant="danger" 
            onClick={handleDeleteSelected}
            icon={<Trash2 />}
          >
            Delete Selected ({selectedFiles.size})
          </Button>
        )}
      </div>

      <div 
        className={`relative border-2 border-dashed rounded-xl p-10 text-center transition-all ${
          dragActive ? 'border-brand-500 bg-brand-50' : 'border-slate-300 bg-white hover:bg-slate-50'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          ref={inputRef}
          type="file" 
          multiple 
          className="hidden" 
          onChange={handleChange} 
          accept=".pst,.eml,.msg"
        />
        
        <div className="flex flex-col items-center gap-3">
          <div className="p-4 bg-slate-100 rounded-full">
            <UploadCloud className={`w-8 h-8 ${dragActive ? 'text-brand-600' : 'text-slate-400'}`} />
          </div>
          <div>
            <p className="text-lg font-medium text-slate-700">
              Drag & drop files here
            </p>
            <p className="text-sm text-slate-500 mt-1">
              or <button onClick={() => inputRef.current?.click()} className="text-brand-600 font-medium hover:underline">browse files</button> on your computer
            </p>
          </div>
        </div>

        {isUploading && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center rounded-xl">
            <div className="flex items-center gap-2 text-brand-700 font-medium">
              <div className="w-2 h-2 bg-brand-600 rounded-full animate-bounce" style={{ animationDelay: '0ms'}} />
              <div className="w-2 h-2 bg-brand-600 rounded-full animate-bounce" style={{ animationDelay: '150ms'}} />
              <div className="w-2 h-2 bg-brand-600 rounded-full animate-bounce" style={{ animationDelay: '300ms'}} />
              Uploading...
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h3 className="font-semibold text-slate-700 text-sm uppercase tracking-wide">
            Staged Files ({files.length})
          </h3>
        </div>
        {files.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No files currently in staging. Upload some to get started.
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {files.map((file, idx) => (
              <li 
                key={file.filename + idx} 
                className={`flex items-center justify-between px-6 py-3 hover:bg-slate-50 cursor-pointer transition-colors ${selectedFiles.has(file.filename) ? 'bg-brand-50 hover:bg-brand-100' : ''}`}
                onClick={() => toggleSelect(file.filename)}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-5 h-5 rounded border flex items-center justify-center ${selectedFiles.has(file.filename) ? 'bg-brand-600 border-brand-600' : 'border-slate-300'}`}>
                    {selectedFiles.has(file.filename) && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
                  </div>
                  <FileIcon className="w-5 h-5 text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-slate-700">{file.filename}</p>
                    <p className="text-xs text-slate-500">{formatSize(file.size)}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};