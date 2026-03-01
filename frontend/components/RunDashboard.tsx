import React, { useEffect, useRef, useState } from 'react';
import { Play, Sparkles, FileText, BarChart2, PieChart as PieIcon, ChevronDown, ChevronUp, Search, Activity, Save } from 'lucide-react';
import { Button } from './Button';
import { RunResponse, MailResult, TechInsightRequest, KeywordStat, RunProgressResponse } from '../types';
import { KeywordChart, ClassChart } from './Charts';

interface RunDashboardProps {
  onRun: () => void;
  onSaveResult?: () => void;
  isRunning: boolean;
  isSavingResult?: boolean;
  canSaveResult?: boolean;
  results: RunResponse | null;
  totalResults?: number;
  hasMoreResults?: boolean;
  isLoadingMoreResults?: boolean;
  onLoadMoreResults?: () => void;
  progress: RunProgressResponse | null;
  onInsightRequest: (req: TechInsightRequest) => void;
}

export const RunDashboard: React.FC<RunDashboardProps> = ({
  onRun,
  onSaveResult,
  isRunning,
  isSavingResult,
  canSaveResult = false,
  results,
  totalResults = 0,
  hasMoreResults = false,
  isLoadingMoreResults = false,
  onLoadMoreResults,
  progress,
  onInsightRequest,
}) => {
  const [expandedMail, setExpandedMail] = useState<number | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const toggleExpand = (idx: number) => {
    setExpandedMail(expandedMail === idx ? null : idx);
  };

  const handleKeywordClick = (k: KeywordStat, category: string) => {
    onInsightRequest({
      keyword: k.keyword,
      count: k.count,
      ratio: k.ratio,
      category
    });
  };

  const progressValue = Math.max(0, Math.min(100, progress?.progress ?? 0));
  const stageLabel = progress?.message || 'Analyzing content and calculating embeddings...';
  const loadedResults = results?.results.length ?? 0;
  const displayedTotal = totalResults > 0 ? totalResults : loadedResults;

  useEffect(() => {
    if (!hasMoreResults || !onLoadMoreResults) return;
    const target = loadMoreRef.current;
    if (!target) return;
    const observer = new IntersectionObserver(
      entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          onLoadMoreResults();
        }
      },
      { rootMargin: '240px 0px' }
    );
    observer.observe(target);
    return () => observer.disconnect();
  }, [hasMoreResults, onLoadMoreResults, loadedResults]);

  if (!results && !isRunning) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="bg-brand-50 p-4 rounded-full mb-4">
          <Play className="w-8 h-8 text-brand-600 ml-1" />
        </div>
        <h3 className="text-xl font-semibold text-slate-800 mb-2">Ready to Process</h3>
        <p className="text-slate-500 mb-6 max-w-md text-center">
          Execute the configured pipeline on the staged files. This may take a moment depending on the file sizes.
        </p>
        <Button size="lg" onClick={onRun} icon={<Play className="w-4 h-4" />}>
          Run Pipeline
        </Button>
      </div>
    );
  }

  if (isRunning && !results) {
    return (
      <div className="py-20">
        <div className="relative overflow-hidden rounded-2xl border border-cyan-300/50 bg-slate-950 px-8 py-10 shadow-[0_0_40px_rgba(6,182,212,0.18)]">
          <div className="pointer-events-none absolute -inset-24 bg-[radial-gradient(circle_at_20%_10%,rgba(14,165,233,0.25),transparent_35%),radial-gradient(circle_at_85%_90%,rgba(56,189,248,0.2),transparent_40%)]"></div>
          <div className="relative flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full border border-cyan-300/60 bg-cyan-500/10 p-2">
                <Activity className="h-5 w-5 text-cyan-300 animate-pulse" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-cyan-200/80">Pipeline Telemetry</p>
                <p className="mt-1 text-lg font-semibold text-cyan-50">Processing Large Mail Batch</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-cyan-200/80">Progress</p>
              <p className="text-3xl font-bold text-cyan-50 tabular-nums">{progressValue.toFixed(1)}%</p>
            </div>
          </div>

          <div className="relative mt-8 h-4 rounded-full border border-cyan-300/30 bg-slate-900/80 p-[2px]">
            <div
              className="h-full rounded-full bg-[linear-gradient(90deg,#06b6d4_0%,#0ea5e9_45%,#22d3ee_100%)] shadow-[0_0_18px_rgba(34,211,238,0.8)] transition-all duration-500 ease-out"
              style={{ width: `${progressValue}%` }}
            />
            <div className="pointer-events-none absolute inset-0 rounded-full bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.28)_50%,transparent_100%)] animate-pulse"></div>
          </div>

          <div className="relative mt-4 flex items-center justify-between text-sm text-cyan-100">
            <p>{stageLabel}</p>
            <p className="font-mono text-cyan-300">
              {(progress?.current ?? 0)}/{Math.max(progress?.total ?? 0, 0)}
            </p>
          </div>

          <div className="relative mt-3 flex items-center gap-2 text-cyan-200/80">
            <Sparkles className="h-4 w-4 animate-pulse" />
            <span className="text-xs tracking-wide">GPU/CPU adaptive semantic engine is running</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header Actions */}
      <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-slate-200 sticky top-0 z-10">
        <div className="flex items-center gap-3">
            <div className={`h-3 w-3 rounded-full ${isRunning ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`} />
            <span className="font-semibold text-slate-700">
              Status: {isRunning ? `Running ${progressValue.toFixed(0)}%` : 'Complete'}
            </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={onSaveResult}
            isLoading={isSavingResult}
            disabled={!results || isRunning || !canSaveResult}
            variant="secondary"
            icon={<Save className="w-4 h-4" />}
          >
            {canSaveResult ? 'Save Result' : 'Saved'}
          </Button>
          <Button onClick={onRun} isLoading={isRunning} variant="secondary" icon={<Play className="w-4 h-4"/>}>
            Rerun
          </Button>
        </div>
      </div>

      {results && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatsCard label="Messages" value={results.summary.message_count} icon={<FileText className="text-blue-500" />} />
            <StatsCard label="Total Blocks" value={results.summary.block_count} icon={<BarChart2 className="text-indigo-500" />} />
            <StatsCard label="Classes Found" value={Object.keys(results.summary.class_summary).length} icon={<PieIcon className="text-emerald-500" />} />
            <StatsCard label="Keyword Categories" value={Object.keys(results.summary.keyword_summary).length} icon={<Search className="text-amber-500" />} />
          </div>

          {/* Visualization Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Top Keywords</h3>
              <div className="space-y-6">
                {Object.entries(results.summary.keyword_summary).map(([category, keywords]) => (
                  <div key={category}>
                    <p className="text-xs font-bold text-slate-500 uppercase mb-2">{category}</p>
                    <KeywordChart 
                        data={keywords} 
                        onBarClick={(data) => handleKeywordClick(data, category)}
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-center text-slate-400 mt-2 italic">Click a bar for Tech Insight</p>
            </div>
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Classification Distribution</h3>
              <ClassChart data={results.summary.class_summary} />
            </div>
          </div>

          {/* Detailed Results List */}
          <div className="space-y-4">
            <div className="flex items-end justify-between px-1">
              <h3 className="text-lg font-semibold text-slate-800">Detailed Analysis</h3>
              <p className="text-xs text-slate-500">
                Loaded {loadedResults} / {displayedTotal}
              </p>
            </div>
            {results.results.map((mail, idx) => (
              <MailCard 
                key={idx} 
                mail={mail} 
                expanded={expandedMail === idx} 
                onToggle={() => toggleExpand(idx)}
                onKeywordClick={handleKeywordClick}
              />
            ))}
            {hasMoreResults && (
              <div ref={loadMoreRef} className="rounded-lg border border-dashed border-slate-300 bg-white/80 px-4 py-3 text-center text-sm text-slate-500">
                {isLoadingMoreResults ? 'Loading more results...' : 'Scroll down to load more'}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// Sub-components for Dashboard
const StatsCard = ({ label, value, icon }: { label: string, value: string | number, icon: React.ReactNode }) => (
  <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 flex items-center justify-between">
    <div>
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
    </div>
    <div className="p-3 bg-slate-50 rounded-lg">
      {icon}
    </div>
  </div>
);

interface MailCardProps {
    mail: MailResult;
    expanded: boolean;
    onToggle: () => void;
    onKeywordClick: (k: KeywordStat, cat: string) => void;
}

const MailCard: React.FC<MailCardProps> = ({ mail, expanded, onToggle, onKeywordClick }) => {
    return (
        <div className={`bg-white rounded-lg shadow-sm border transition-all ${expanded ? 'ring-2 ring-brand-500 border-transparent' : 'border-slate-200 hover:border-brand-300'}`}>
            <div className="p-4 cursor-pointer flex items-center justify-between" onClick={onToggle}>
                <div className="flex items-center gap-4 overflow-hidden">
                    <div className={`p-2 rounded-full ${mail.semantic?.matched ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-500'}`}>
                        <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                        <h4 className="font-medium text-slate-800 truncate">{mail.subject || "(No Subject)"}</h4>
                        <p className="text-xs text-slate-500 truncate">{mail.source_path}</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    {mail.semantic && (
                        <span className="px-2 py-1 text-xs font-bold bg-slate-100 text-slate-600 rounded">
                            Score: {mail.semantic.score.toFixed(2)}
                        </span>
                    )}
                    {expanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                </div>
            </div>

            {expanded && (
                <div className="border-t border-slate-100 p-4 bg-slate-50/50 rounded-b-lg">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Semantic Match Info */}
                        <div>
                            <h5 className="text-xs font-bold uppercase text-slate-500 mb-2">Semantic Match</h5>
                            {mail.semantic ? (
                                <div className="bg-white p-3 rounded border border-slate-200 text-sm">
                                    <p className="text-slate-800 mb-2 font-serif italic">"{mail.semantic.text}"</p>
                                    <div className="flex gap-2 text-xs text-slate-500">
                                        <span>Lines: {mail.semantic.start_line}-{mail.semantic.end_line}</span>
                                        <span>|</span>
                                        <span className={mail.semantic.matched ? "text-emerald-600 font-medium" : "text-amber-600"}>
                                            {mail.semantic.matched ? "Matched" : "Low Confidence"}
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <p className="text-sm text-slate-400 italic">No semantic match found.</p>
                            )}
                        </div>

                        {/* Aggregation Summary */}
                        <div>
                            <h5 className="text-xs font-bold uppercase text-slate-500 mb-2">Analysis Summary</h5>
                            <div className="space-y-3">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-600">Blocks:</span>
                                    <span className="font-mono text-slate-900">{mail.aggregation.block_count}</span>
                                </div>
                                <div>
                                    <span className="text-xs text-slate-500">Class:</span>
                                    <div className="flex gap-2 mt-1">
                                        {Object.entries(mail.aggregation.class_summary).map(([cls, stat]) => (
                                            <span key={cls} className="px-2 py-0.5 bg-white border border-slate-200 rounded text-xs text-slate-600">
                                                {cls}: {stat.count}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <div>
                                    <span className="text-xs text-slate-500">Keywords:</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {Object.entries(mail.aggregation.keyword_summary).flatMap(([cat, keywords]) => 
                                            keywords.map(k => (
                                                <button 
                                                    key={`${cat}-${k.keyword}`}
                                                    onClick={(e) => { e.stopPropagation(); onKeywordClick(k, cat); }}
                                                    className="px-2 py-0.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded text-xs transition-colors"
                                                >
                                                    {k.keyword}
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
