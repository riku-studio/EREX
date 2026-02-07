import React from 'react';
import { Archive, RefreshCw, Trash2, Clock3, FileText, BarChart3, Search } from 'lucide-react';
import { Button } from './Button';
import { HistoryItem, HistoryRecord } from '../types';

interface HistoryPanelProps {
  items: HistoryItem[];
  selectedId: string | null;
  selectedRecord: HistoryRecord | null;
  loadingList: boolean;
  loadingDetail: boolean;
  onRefresh: () => void;
  onSelect: (recordId: string) => void;
  onDelete: (recordId: string) => void;
}

const formatDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

export const HistoryPanel: React.FC<HistoryPanelProps> = ({
  items,
  selectedId,
  selectedRecord,
  loadingList,
  loadingDetail,
  onRefresh,
  onSelect,
  onDelete,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <Archive className="w-5 h-5 text-brand-600" />
            Run History
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Hand-saved pipeline outputs. Automatic save is disabled by default.
          </p>
        </div>
        <Button variant="secondary" onClick={onRefresh} isLoading={loadingList} icon={<RefreshCw className="w-4 h-4" />}>
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 text-sm font-semibold text-slate-700">
            Saved Runs ({items.length})
          </div>
          {items.length === 0 ? (
            <div className="p-6 text-sm text-slate-500">No saved records yet. Run pipeline and click Save.</div>
          ) : (
            <ul className="divide-y divide-slate-100 max-h-[68vh] overflow-y-auto">
              {items.map((item) => (
                <li
                  key={item.id}
                  className={`px-4 py-3 cursor-pointer transition-colors ${
                    selectedId === item.id ? 'bg-brand-50' : 'hover:bg-slate-50'
                  }`}
                  onClick={() => onSelect(item.id)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800 truncate">{item.title || `Run ${item.id.slice(0, 8)}`}</p>
                      <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                        <Clock3 className="w-3 h-3" />
                        {formatDate(item.saved_at)}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        Msg {item.summary.message_count} · Blocks {item.summary.block_count}
                      </p>
                    </div>
                    <button
                      className="p-1.5 rounded text-slate-400 hover:text-red-600 hover:bg-red-50"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(item.id);
                      }}
                      title="Delete record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm">
          {!selectedId && (
            <div className="p-8 text-slate-500 text-sm">Select a saved run on the left to inspect details.</div>
          )}

          {selectedId && loadingDetail && (
            <div className="p-8 text-slate-500 text-sm">Loading selected history record...</div>
          )}

          {selectedRecord && !loadingDetail && (
            <div className="p-5 space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">{selectedRecord.title || `Run ${selectedRecord.id}`}</h3>
                  <p className="text-sm text-slate-500 mt-1">{formatDate(selectedRecord.saved_at)}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Stat label="Messages" value={selectedRecord.result.summary.message_count} icon={<FileText className="w-4 h-4 text-blue-500" />} />
                <Stat label="Blocks" value={selectedRecord.result.summary.block_count} icon={<BarChart3 className="w-4 h-4 text-indigo-500" />} />
                <Stat label="Class Types" value={Object.keys(selectedRecord.result.summary.class_summary || {}).length} />
                <Stat label="Keyword Cats" value={Object.keys(selectedRecord.result.summary.keyword_summary || {}).length} />
              </div>

              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <Search className="w-4 h-4 text-brand-600" />
                  Top Keywords
                </h4>
                {Object.keys(selectedRecord.result.summary.keyword_summary || {}).length === 0 ? (
                  <p className="text-sm text-slate-500">No keyword summary in this run.</p>
                ) : (
                  <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1">
                    {Object.entries(selectedRecord.result.summary.keyword_summary).map(([category, keywords]) => (
                      <div key={category} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">{category}</p>
                        {keywords.length === 0 ? (
                          <p className="text-xs text-slate-500">No keywords</p>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {keywords.slice(0, 20).map((keyword) => (
                              <span
                                key={`${category}-${keyword.keyword}`}
                                className="inline-flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 px-2.5 py-1 text-xs text-brand-700"
                              >
                                <span className="font-semibold">{keyword.keyword}</span>
                                <span className="text-brand-500">· {keyword.count}</span>
                                <span className="text-brand-500">· {(keyword.ratio * 100).toFixed(1)}%</span>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const Stat = ({ label, value, icon }: { label: string; value: string | number; icon?: React.ReactNode }) => (
  <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
    <div className="flex items-center justify-between">
      <p className="text-xs text-slate-500">{label}</p>
      {icon || null}
    </div>
    <p className="mt-1 text-xl font-bold text-slate-800">{value}</p>
  </div>
);
