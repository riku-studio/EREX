import React, { useState, useEffect } from 'react';
import { LayoutDashboard, FolderOpen, Settings, Info, Archive } from 'lucide-react';

import { api } from './services/api';
import { 
  PipelineConfig, 
  UploadResponseItem, 
  RunResponse, 
  RunProgressResponse,
  HistoryItem,
  HistoryRecord,
  TabView, 
  TechInsightRequest,
  TechInsightResponse
} from './types';

import { ConfigPanel } from './components/ConfigPanel';
import { FileManager } from './components/FileManager';
import { RunDashboard } from './components/RunDashboard';
import { TechInsightModal } from './components/TechInsightModal';
import { HistoryPanel } from './components/HistoryPanel';

const App: React.FC = () => {
  const RESULT_PAGE_SIZE = 500;
  // Navigation State
  const [activeTab, setActiveTab] = useState<TabView>('dashboard');

  // Application Data State
  const [config, setConfig] = useState<PipelineConfig | null>(null);
  const [files, setFiles] = useState<UploadResponseItem[]>([]);
  const [runResults, setRunResults] = useState<RunResponse | null>(null);
  const [runJobId, setRunJobId] = useState<string | null>(null);
  const [runTotal, setRunTotal] = useState<number>(0);
  const [nextResultOffset, setNextResultOffset] = useState<number>(0);
  const [hasMoreResults, setHasMoreResults] = useState<boolean>(false);
  const [runProgress, setRunProgress] = useState<RunProgressResponse | null>(null);
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [historyDetail, setHistoryDetail] = useState<HistoryRecord | null>(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);
  
  // Loading States
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);
  const [insightLoading, setInsightLoading] = useState(false);
  const [savingHistory, setSavingHistory] = useState(false);
  const [loadingMoreResults, setLoadingMoreResults] = useState(false);
  const [loadingHistoryList, setLoadingHistoryList] = useState(false);
  const [loadingHistoryDetail, setLoadingHistoryDetail] = useState(false);

  const [activeRunHistoryId, setActiveRunHistoryId] = useState<string | null>(null);

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
    loadHistory();
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
    setRunJobId(null);
    setRunTotal(0);
    setNextResultOffset(0);
    setHasMoreResults(false);
    setRunProgress(null);
    setActiveRunHistoryId(null);
    try {
      const started = await api.startPipelineRun();
      setRunJobId(started.job_id);
      let progress = await api.getPipelineProgress(started.job_id);
      setRunProgress(progress);

      while (progress.status === 'queued' || progress.status === 'running') {
        await new Promise(resolve => setTimeout(resolve, 600));
        progress = await api.getPipelineProgress(started.job_id);
        setRunProgress(progress);
      }

      if (progress.status === 'failed') {
        throw new Error(progress.error || 'Pipeline job failed');
      }

      const firstPage = await api.getPipelineResultPage(started.job_id, 0, RESULT_PAGE_SIZE);
      setRunResults({
        results: firstPage.results,
        summary: firstPage.summary,
      });
      setRunTotal(firstPage.total);
      setNextResultOffset(firstPage.offset + firstPage.results.length);
      setHasMoreResults(firstPage.has_more);
      setToast({ msg: 'Pipeline finished successfully', type: 'success' });
    } catch (err) {
      console.error(err);
      setToast({ msg: 'Pipeline run failed', type: 'error' });
    } finally {
      setRunning(false);
    }
  };

  const handleLoadMoreResults = async () => {
    if (!runJobId || !hasMoreResults || loadingMoreResults || running) return;
    setLoadingMoreResults(true);
    try {
      const page = await api.getPipelineResultPage(runJobId, nextResultOffset, RESULT_PAGE_SIZE);
      setRunResults(prev => ({
        summary: page.summary,
        results: [...(prev?.results || []), ...page.results],
      }));
      setRunTotal(page.total);
      setNextResultOffset(page.offset + page.results.length);
      setHasMoreResults(page.has_more);
    } catch (err) {
      setToast({ msg: 'Failed to load more results', type: 'error' });
    } finally {
      setLoadingMoreResults(false);
    }
  };

  const loadHistory = async () => {
    setLoadingHistoryList(true);
    try {
      const items = await api.listPipelineHistory();
      setHistoryItems(items);
      if (items.length === 0) {
        setSelectedHistoryId(null);
        setHistoryDetail(null);
      }
    } catch (err) {
      setToast({ msg: 'Failed to load history', type: 'error' });
    } finally {
      setLoadingHistoryList(false);
    }
  };

  const handleSaveRunResult = async () => {
    if ((!runResults && !runJobId) || activeRunHistoryId) return;
    setSavingHistory(true);
    try {
      const fullResult = runJobId ? await api.getPipelineResult(runJobId) : runResults!;
      const saved = await api.savePipelineHistory(fullResult);
      setActiveRunHistoryId(saved.id);
      setToast({ msg: 'Run result saved', type: 'success' });
      await loadHistory();
    } catch (err) {
      setToast({ msg: 'Failed to save run result', type: 'error' });
    } finally {
      setSavingHistory(false);
    }
  };

  const handleSelectHistory = async (recordId: string) => {
    setSelectedHistoryId(recordId);
    setLoadingHistoryDetail(true);
    try {
      const detail = await api.getPipelineHistory(recordId);
      setHistoryDetail(detail);
    } catch (err) {
      setToast({ msg: 'Failed to load history detail', type: 'error' });
    } finally {
      setLoadingHistoryDetail(false);
    }
  };

  const handleDeleteHistory = async (recordId: string) => {
    if (!confirm('Delete this history record?')) return;
    try {
      await api.deletePipelineHistory(recordId);
      setToast({ msg: 'History record deleted', type: 'success' });
      if (selectedHistoryId === recordId) {
        setSelectedHistoryId(null);
        setHistoryDetail(null);
      }
      await loadHistory();
    } catch (err) {
      setToast({ msg: 'Failed to delete history record', type: 'error' });
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
          <NavButton 
            active={activeTab === 'history'} 
            onClick={() => setActiveTab('history')} 
            icon={<Archive size={18}/>} 
            label="History"
            badge={historyItems.length > 0 ? historyItems.length : undefined}
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
              onSaveResult={handleSaveRunResult}
              isRunning={running} 
              isSavingResult={savingHistory}
              canSaveResult={!!runResults && !activeRunHistoryId}
              results={runResults}
              totalResults={runTotal}
              hasMoreResults={hasMoreResults}
              isLoadingMoreResults={loadingMoreResults}
              onLoadMoreResults={handleLoadMoreResults}
              progress={runProgress}
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
              onConfigUpdated={(cfg) => setConfig(cfg)}
            />
          )}
          {activeTab === 'history' && (
            <HistoryPanel
              items={historyItems}
              selectedId={selectedHistoryId}
              selectedRecord={historyDetail}
              loadingList={loadingHistoryList}
              loadingDetail={loadingHistoryDetail}
              onRefresh={loadHistory}
              onSelect={handleSelectHistory}
              onDelete={handleDeleteHistory}
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
