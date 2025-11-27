import React, { useState } from 'react';
import { Play, Sparkles, FileText, BarChart2, PieChart as PieIcon, ChevronDown, ChevronUp, Search, Info } from 'lucide-react';
import { Button } from './Button';
import { RunResponse, MailResult, TechInsightRequest, KeywordStat } from '../types';
import { KeywordChart, ClassChart } from './Charts';

interface RunDashboardProps {
  onRun: () => void;
  isRunning: boolean;
  results: RunResponse | null;
  onInsightRequest: (req: TechInsightRequest) => void;
}

export const RunDashboard: React.FC<RunDashboardProps> = ({ onRun, isRunning, results, onInsightRequest }) => {
  const [expandedMail, setExpandedMail] = useState<number | null>(null);

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
      <div className="flex flex-col items-center justify-center py-32">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-slate-200 border-t-brand-600 rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-brand-500 animate-pulse" />
          </div>
        </div>
        <p className="mt-6 text-lg font-medium text-slate-700">Processing Pipeline...</p>
        <p className="text-slate-500">Analyzing content, extracting keywords, and classifying.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header Actions */}
      <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-slate-200 sticky top-0 z-10">
        <div className="flex items-center gap-3">
            <div className={`h-3 w-3 rounded-full ${isRunning ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`} />
            <span className="font-semibold text-slate-700">Status: {isRunning ? 'Running...' : 'Complete'}</span>
        </div>
        <Button onClick={onRun} isLoading={isRunning} variant="secondary" icon={<Play className="w-4 h-4"/>}>
          Rerun
        </Button>
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
            <h3 className="text-lg font-semibold text-slate-800 pl-1">Detailed Analysis</h3>
            {results.results.map((mail, idx) => (
              <MailCard 
                key={idx} 
                mail={mail} 
                expanded={expandedMail === idx} 
                onToggle={() => toggleExpand(idx)}
                onKeywordClick={handleKeywordClick}
              />
            ))}
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
