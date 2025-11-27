import React, { useState, useEffect } from 'react';
import { LayoutDashboard, FolderOpen, Settings, Info } from 'lucide-react';

import { api } from './services/api';
import { 
  PipelineConfig, 
  UploadResponseItem, 
  RunResponse, 
  TabView, 
  TechInsightRequest,
  TechInsightResponse
} from './types';

import { ConfigPanel } from './components/ConfigPanel';
import { FileManager } from './components/FileManager';
import { RunDashboard } from './components/RunDashboard';
import { TechInsightModal } from './components/TechInsightModal';

const App: React.FC = () => {
  // Navigation State
  const [activeTab, setActiveTab] = useState<TabView>('dashboard');

  // Application Data State
  const [config, setConfig] = useState<PipelineConfig | null>(null);
  const [files, setFiles] = useState<UploadResponseItem[]>([]);
  const [runResults, setRunResults] = useState<RunResponse | null>(null);
  
  // Loading States
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);

  // Modal State
  const [insightModal, setInsightModal] = useState<{ isOpen: boolean; keyword: string | null; data: TechInsightResponse | null }>({
    isOpen: false,
    keyword: null,
    data: null
  });

  // Notification (Simple Toast)
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadConfig();
    loadFiles();
  }, []);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const loadConfig = async () => {
    setLoadingConfig(true);
    try {
      const data = await api.fetchConfig();
      setConfig(data);
    } catch (err) {
      console.error(err);
      setToast({ msg: 'Failed to load config', type: 'error' });
    } finally {
      setLoadingConfig(false);
    }
  };

  const loadFiles = async () => {
    try {
      const list = await api.listFiles();
      setFiles(list);
    } catch (err) {
      setToast({ msg: 'Failed to load files', type: 'error' });
    }
  }

  const handleUpload = async (fileList: File[]) => {
    setUploading(true);
    try {
      const response = await api.uploadFiles(fileList);
      setFiles(prev => [...prev, ...response]);
      setToast({ msg: `Uploaded ${fileList.length} files`, type: 'success' });
    } catch (err) {
      setToast({ msg: 'Upload failed', type: 'error' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (filenames: string[]) => {
    try {
      await api.deleteFiles(filenames);
      setFiles(prev => prev.filter(f => !filenames.includes(f.filename)));
      setToast({ msg: 'Files deleted', type: 'success' });
    } catch (err) {
      setToast({ msg: 'Delete failed', type: 'error' });
    }
  };

  const handleRun = async () => {
    setRunning(true);
    setRunResults(null);
    try {
      const results = await api.runPipeline();
      setRunResults(results);
      setToast({ msg: 'Pipeline finished successfully', type: 'success' });
    } catch (err) {
      setToast({ msg: 'Pipeline run failed', type: 'error' });
    } finally {
      setRunning(false);
    }
  };

  const handleTechInsight = async (req: TechInsightRequest) => {
    setInsightModal({ isOpen: true, keyword: req.keyword, data: null });
    setInsightLoading(true);
    try {
      const data = await api.getTechInsight(req);
      setInsightModal(prev => ({ ...prev, data }));
    } catch (err) {
      setToast({ msg: 'Failed to get insight', type: 'error' });
      setInsightModal(prev => ({ ...prev, isOpen: false }));
    } finally {
      setInsightLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-50 text-slate-800 font-sans">
      
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 bg-white border-r border-slate-200 flex-shrink-0">
        <div className="p-6 border-b border-slate-100">
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center text-white font-bold">E</div>
            EREX Pipeline
          </h1>
        </div>
        <nav className="p-4 space-y-1">
          <NavButton 
            active={activeTab === 'dashboard'} 
            onClick={() => setActiveTab('dashboard')} 
            icon={<LayoutDashboard size={18}/>} 
            label="Run Dashboard" 
          />
          <NavButton 
            active={activeTab === 'files'} 
            onClick={() => setActiveTab('files')} 
            icon={<FolderOpen size={18}/>} 
            label="Files" 
            badge={files.length > 0 ? files.length : undefined}
          />
          <NavButton 
            active={activeTab === 'config'} 
            onClick={() => setActiveTab('config')} 
            icon={<Settings size={18}/>} 
            label="Configuration" 
          />
        </nav>
        
        <div className="absolute bottom-0 w-full md:w-64 p-4 border-t border-slate-100 bg-slate-50/50">
           <div className="flex items-start gap-3 text-xs text-slate-500">
              <Info className="w-4 h-4 mt-0.5 shrink-0" />
              <p>System Ready. <br/>Backend connected.</p>
           </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto h-screen p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          {activeTab === 'dashboard' && (
            <RunDashboard 
              onRun={handleRun} 
              isRunning={running} 
              results={runResults}
              onInsightRequest={handleTechInsight}
            />
          )}
          {activeTab === 'files' && (
            <FileManager 
              files={files} 
              isUploading={uploading} 
              onUpload={handleUpload}
              onDelete={handleDelete}
            />
          )}
          {activeTab === 'config' && (
            <ConfigPanel 
              config={config} 
              loading={loadingConfig} 
              onRefresh={loadConfig} 
            />
          )}
        </div>
      </main>

      {/* Modals & Overlays */}
      <TechInsightModal 
        isOpen={insightModal.isOpen}
        onClose={() => setInsightModal(prev => ({...prev, isOpen: false}))}
        loading={insightLoading}
        keyword={insightModal.keyword}
        data={insightModal.data}
      />

      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-6 right-6 px-4 py-3 rounded-lg shadow-lg text-sm font-medium animate-in slide-in-from-bottom-5 duration-300 ${
          toast.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'
        }`}>
          {toast.msg}
        </div>
      )}
    </div>
  );
};

const NavButton = ({ active, onClick, icon, label, badge }: any) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      active 
        ? 'bg-brand-50 text-brand-700' 
        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
    }`}
  >
    <div className="flex items-center gap-3">
      {icon}
      <span>{label}</span>
    </div>
    {badge !== undefined && (
      <span className="bg-slate-200 text-slate-600 text-xs px-2 py-0.5 rounded-full font-bold">
        {badge}
      </span>
    )}
  </button>
);

export default App;
