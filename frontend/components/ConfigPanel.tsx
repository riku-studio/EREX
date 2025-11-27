import React from 'react';
import { PipelineConfig } from '../types';
import { RefreshCw, Server, Settings } from 'lucide-react';
import { Button } from './Button';

interface ConfigPanelProps {
  config: PipelineConfig | null;
  loading: boolean;
  onRefresh: () => void;
}

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, loading, onRefresh }) => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <Settings className="w-5 h-5 text-slate-500" />
            Pipeline Configuration
          </h2>
          <p className="text-slate-500 text-sm mt-1">Current runtime settings and enabled steps.</p>
        </div>
        <Button variant="secondary" onClick={onRefresh} isLoading={loading} icon={<RefreshCw />}>
          Refresh
        </Button>
      </div>

      {!config && !loading && (
        <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-200 border-dashed">
          <p className="text-slate-500">No configuration loaded.</p>
        </div>
      )}

      {config && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Active Steps Card */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4 flex items-center gap-2">
              <Server className="w-4 h-4" />
              Active Steps
            </h3>
            <div className="flex flex-wrap gap-2">
              {config.steps.map((step, idx) => (
                <div key={idx} className="flex items-center">
                  <span className="px-3 py-1 bg-brand-50 text-brand-700 rounded-full text-sm font-medium border border-brand-100">
                    {step}
                  </span>
                  {idx < config.steps.length - 1 && (
                    <div className="w-4 h-0.5 bg-slate-200 mx-1" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Config Summary Card */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">
              Parameters
            </h3>
            <div className="overflow-hidden rounded-lg border border-slate-100">
              <table className="min-w-full divide-y divide-slate-100">
                <tbody className="divide-y divide-slate-100 bg-white">
                  {Object.entries(config.summary).map(([key, value]) => (
                    <tr key={key}>
                      <td className="whitespace-nowrap py-3 pl-4 pr-3 text-sm font-medium text-slate-600">
                        {key}
                      </td>
                      <td className="whitespace-nowrap py-3 pl-3 pr-4 text-sm text-slate-800 font-mono text-right">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};