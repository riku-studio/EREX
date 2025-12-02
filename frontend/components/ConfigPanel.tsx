import React, { useEffect, useState } from 'react';
import { PipelineConfig, PipelineConfigUpdatePayload } from '../types';
import { RefreshCw, Server, Settings, Save, AlertCircle, Database } from 'lucide-react';
import { Button } from './Button';
import { api } from '../services/api';

interface ConfigPanelProps {
  config: PipelineConfig | null;
  loading: boolean;
  onRefresh: () => void;
  onConfigUpdated?: (cfg: PipelineConfig) => void;
}

interface FormState {
  steps: string;
  lineFilter: string;
  semanticTemplates: string;
  keywordsTech: string;
  indexRules: string;
  classifierForeigner: string;
}

const formatJson = (value: Record<string, any> | undefined) => {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return '';
  }
};

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, loading, onRefresh, onConfigUpdated }) => {
  const [form, setForm] = useState<FormState>({
    steps: '',
    lineFilter: '',
    semanticTemplates: '',
    keywordsTech: '',
    indexRules: '',
    classifierForeigner: '',
  });
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    if (!config) return;
    setForm({
      steps: config.steps.join(', '),
      lineFilter: formatJson(config.line_filter),
      semanticTemplates: formatJson(config.semantic_templates),
      keywordsTech: formatJson(config.keywords_tech),
      indexRules: formatJson(config.index_rules),
      classifierForeigner: formatJson(config.classifier_foreigner),
    });
  }, [config]);

  const parseJsonField = (label: string, value: string) => {
    try {
      return value.trim() ? JSON.parse(value) : {};
    } catch (err: any) {
      throw new Error(`${label} JSON parse failed: ${err?.message || err}`);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setStatus(null);
    try {
      const payload: PipelineConfigUpdatePayload = {
        steps: form.steps.split(',').map(s => s.trim()).filter(Boolean),
        line_filter: parseJsonField('Line Filter', form.lineFilter),
        semantic_templates: parseJsonField('Semantic Templates', form.semanticTemplates),
        keywords_tech: parseJsonField('Keywords', form.keywordsTech),
        index_rules: parseJsonField('Index Rules', form.indexRules),
        classifier_foreigner: parseJsonField('Classifier', form.classifierForeigner),
      };
      const saved = await api.updateConfig(payload);
      setStatus({ type: 'success', message: 'Saved to database' });
      setForm({
        steps: saved.steps.join(', '),
        lineFilter: formatJson(saved.line_filter),
        semanticTemplates: formatJson(saved.semantic_templates),
        keywordsTech: formatJson(saved.keywords_tech),
        indexRules: formatJson(saved.index_rules),
        classifierForeigner: formatJson(saved.classifier_foreigner),
      });
      onConfigUpdated?.(saved);
    } catch (err: any) {
      setStatus({ type: 'error', message: err?.message || 'Save failed' });
    } finally {
      setSaving(false);
    }
  };

  const renderJsonArea = (label: string, value: string, onChange: (v: string) => void, rows = 10) => (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-700">{label}</p>
        <span className="text-[11px] uppercase tracking-wide text-slate-400">JSON</span>
      </div>
      <textarea
        className="w-full font-mono text-xs rounded-lg border border-slate-200 focus:border-brand-500 focus:ring-brand-200 p-3 bg-slate-50/50 min-h-[140px]"
        value={value}
        rows={rows}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );

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
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onRefresh} isLoading={loading} icon={<RefreshCw />}>
            Refresh
          </Button>
          <Button onClick={handleSave} isLoading={saving || loading} icon={<Save className="w-4 h-4" />} disabled={!config}>
            Save
          </Button>
        </div>
      </div>

      {!config && !loading && (
        <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-200 border-dashed">
          <p className="text-slate-500">No configuration loaded.</p>
        </div>
      )}

      {config && (
        <div className="space-y-4">
          {status && (
            <div
              className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${
                status.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-red-50 text-red-700 border border-red-100'
              }`}
            >
              <AlertCircle className="w-4 h-4" />
              <span>{status.message}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Active Steps Card */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-slate-500" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Active Steps</h3>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Database className="w-4 h-4" />
                  <span>{config.source === 'db' ? 'Database' : 'File fallback'}</span>
                </div>
              </div>
              <p className="text-xs text-slate-500">Comma separated</p>
              <input
                className="w-full rounded-lg border border-slate-200 focus:border-brand-500 focus:ring-brand-200 px-3 py-2 text-sm"
                value={form.steps}
                onChange={(e) => setForm((prev) => ({ ...prev, steps: e.target.value }))}
                placeholder="cleaner,line_filter,semantic,splitter,extractor,classifier,aggregator"
              />
              <div className="flex flex-wrap gap-2">
                {config.steps.map((step, idx) => (
                  <div key={`${step}-${idx}`} className="flex items-center">
                    <span className="px-3 py-1 bg-brand-50 text-brand-700 rounded-full text-sm font-medium border border-brand-100">
                      {step}
                    </span>
                    {idx < config.steps.length - 1 && <div className="w-4 h-0.5 bg-slate-200 mx-1" />}
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

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderJsonArea('Line Filter', form.lineFilter, (v) => setForm((prev) => ({ ...prev, lineFilter: v })))}
            {renderJsonArea('Semantic Templates', form.semanticTemplates, (v) =>
              setForm((prev) => ({ ...prev, semanticTemplates: v }))
            )}
            {renderJsonArea('Keywords', form.keywordsTech, (v) => setForm((prev) => ({ ...prev, keywordsTech: v })), 14)}
            {renderJsonArea('Index Rules', form.indexRules, (v) => setForm((prev) => ({ ...prev, indexRules: v })), 8)}
            {renderJsonArea('Classifier', form.classifierForeigner, (v) =>
              setForm((prev) => ({ ...prev, classifierForeigner: v }))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
