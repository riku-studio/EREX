import React, { useEffect, useState } from 'react';
import { PipelineConfig, PipelineConfigUpdatePayload } from '../types';
import { 
  RefreshCw, Server, Settings, Save, AlertCircle, Database, 
  Plus, X, Hash, ListTree, Tags, KeyRound, ChevronRight
} from 'lucide-react';
import { Button } from './Button';
import { api } from '../services/api';

interface ConfigPanelProps {
  config: PipelineConfig | null;
  loading: boolean;
  onRefresh: () => void;
  onConfigUpdated?: (cfg: PipelineConfig) => void;
}

// --- Helper Components ---

/**
 * A component for editing a list of strings (e.g., Pipeline Steps)
 */
const TagListEditor: React.FC<{
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
}> = ({ label, items, onChange, placeholder }) => {
  const [input, setInput] = useState('');

  const addItem = () => {
    if (input.trim() && !items.includes(input.trim())) {
      onChange([...items, input.trim()]);
      setInput('');
    }
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
        <ListTree className="w-4 h-4 text-brand-500" /> {label}
      </h3>
      <div className="flex flex-wrap gap-2 mb-3">
        {items.map((item, idx) => (
          <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium bg-brand-50 text-brand-700 border border-brand-100 group">
            {item}
            <button onClick={() => removeItem(idx)} className="ml-1.5 text-brand-400 hover:text-brand-600 transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </span>
        ))}
        {items.length === 0 && <span className="text-xs text-slate-400 italic">No items added</span>}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addItem())}
          placeholder={placeholder}
          className="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none"
        />
        <Button size="sm" variant="secondary" onClick={addItem} icon={<Plus className="w-4 h-4" />}>Add</Button>
      </div>
    </div>
  );
};

/**
 * A component for editing key-value pairs (e.g., index_rules)
 */
const KeyValueEditor: React.FC<{
  label: string;
  data: Record<string, any>;
  onChange: (data: Record<string, any>) => void;
  icon?: React.ReactNode;
}> = ({ label, data, onChange, icon }) => {
  const [entries, setEntries] = useState<[string, string][]>([]);

  useEffect(() => {
    setEntries(Object.entries(data || {}).map(([k, v]) => [k, typeof v === 'object' ? JSON.stringify(v) : String(v)]));
  }, [data]);

  const updateEntry = (index: number, key: string, val: string) => {
    const next = [...entries];
    next[index] = [key, val];
    setEntries(next);
    sync(next);
  };

  const addEntry = () => {
    setEntries([...entries, ['', '']]);
  };

  const removeEntry = (index: number) => {
    const next = entries.filter((_, i) => i !== index);
    setEntries(next);
    sync(next);
  };

  const sync = (currentEntries: [string, string][]) => {
    const result: Record<string, any> = {};
    currentEntries.forEach(([k, v]) => {
      if (k.trim()) {
        try {
          // Try to parse as JSON if it looks like an object/array, otherwise keep as string
          if ((v.startsWith('{') && v.endsWith('}')) || (v.startsWith('[') && v.endsWith(']'))) {
            result[k.trim()] = JSON.parse(v);
          } else if (!isNaN(Number(v)) && v.trim() !== '') {
            result[k.trim()] = Number(v);
          } else {
            result[k.trim()] = v;
          }
        } catch {
          result[k.trim()] = v;
        }
      }
    });
    onChange(result);
  };

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
        {icon || <KeyRound className="w-4 h-4 text-indigo-500" />} {label}
      </h3>
      <div className="space-y-2 mb-4">
        {entries.map(([key, val], idx) => (
          <div key={idx} className="flex gap-2 items-center">
            <input
              placeholder="Key"
              value={key}
              onChange={(e) => updateEntry(idx, e.target.value, val)}
              className="w-1/3 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-mono bg-slate-50"
            />
            <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
            <input
              placeholder="Value"
              value={val}
              onChange={(e) => updateEntry(idx, key, e.target.value)}
              className="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
            />
            <button onClick={() => removeEntry(idx)} className="p-1.5 text-slate-400 hover:text-red-500 transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
        {entries.length === 0 && <p className="text-xs text-slate-400 italic py-2 text-center border border-dashed rounded-lg">No parameters defined</p>}
      </div>
      <Button size="sm" variant="ghost" className="w-full border border-dashed border-slate-200 hover:border-brand-300" onClick={addEntry} icon={<Plus className="w-4 h-4" />}>
        Add Field
      </Button>
    </div>
  );
};

/**
 * Special editor for technical keywords grouped by category
 */
const KeywordCategoryEditor: React.FC<{
  data: Record<string, string[]>;
  onChange: (data: Record<string, string[]>) => void;
}> = ({ data, onChange }) => {
  const [newCat, setNewCat] = useState('');

  const addCategory = () => {
    if (newCat.trim() && !data[newCat.trim()]) {
      onChange({ ...data, [newCat.trim()]: [] });
      setNewCat('');
    }
  };

  const removeCategory = (cat: string) => {
    const next = { ...data };
    delete next[cat];
    onChange(next);
  };

  const updateKeywords = (cat: string, words: string[]) => {
    onChange({ ...data, [cat]: words });
  };

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm col-span-1 md:col-span-2">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <Tags className="w-4 h-4 text-emerald-500" /> Keywords Analysis Library
        </h3>
        <div className="flex gap-2">
          <input
            placeholder="New Category Name..."
            value={newCat}
            onChange={(e) => setNewCat(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs outline-none focus:ring-2 focus:ring-brand-500/20"
          />
          <Button size="sm" variant="secondary" onClick={addCategory} icon={<Plus />}>New Category</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(data || {}).map(([cat, words]) => (
          <div key={cat} className="p-4 rounded-xl bg-slate-50 border border-slate-200 relative group">
            <button 
              onClick={() => removeCategory(cat)}
              className="absolute top-2 right-2 p-1 text-slate-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
            >
              <X className="w-4 h-4" />
            </button>
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Hash className="w-3.5 h-3.5" /> {cat}
            </h4>
            <TagListEditor 
              label="" 
              items={words} 
              onChange={(newWords) => updateKeywords(cat, newWords)} 
              placeholder="Add keyword..."
            />
          </div>
        ))}
        {Object.keys(data || {}).length === 0 && (
          <div className="col-span-2 py-10 text-center border-2 border-dashed border-slate-200 rounded-xl text-slate-400">
            No keyword categories defined. Add one to start tracking terms.
          </div>
        )}
      </div>
    </div>
  );
};

// --- Main Component ---

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ config, loading, onRefresh, onConfigUpdated }) => {
  const [localConfig, setLocalConfig] = useState<PipelineConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const handleUpdate = (updates: Partial<PipelineConfigUpdatePayload>) => {
    if (!localConfig) return;
    setLocalConfig({
      ...localConfig,
      ...updates
    } as PipelineConfig);
  };

  const handleSave = async () => {
    if (!localConfig) return;
    setSaving(true);
    setStatus(null);
    try {
      // Cast to any to satisfy compiler when properties are missing from the local type definition
      const cfg = localConfig as any;
      const payload: PipelineConfigUpdatePayload = {
        steps: cfg.steps,
        line_filter: cfg.line_filter,
        semantic_templates: cfg.semantic_templates,
        keywords_tech: cfg.keywords_tech,
        index_rules: cfg.index_rules,
        classifier_foreigner: cfg.classifier_foreigner,
      };
      const saved = await api.updateConfig(payload);
      setStatus({ type: 'success', message: 'Configuration successfully updated in the database.' });
      onConfigUpdated?.(saved);
    } catch (err: any) {
      setStatus({ type: 'error', message: err?.message || 'Failed to save configuration.' });
    } finally {
      setSaving(false);
    }
  };

  if (!localConfig && loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <RefreshCw className="w-8 h-8 text-brand-600 animate-spin mb-4" />
        <p className="text-slate-500">Loading pipeline settings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-20">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
            <div className="p-2 bg-brand-50 rounded-lg">
              <Settings className="w-6 h-6 text-brand-600" />
            </div>
            Pipeline Parameters
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Configure how the EREX agent processes, classifies, and extracts insights from your data.
          </p>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <Button variant="secondary" onClick={onRefresh} isLoading={loading} icon={<RefreshCw />}>
            Reset to Last Save
          </Button>
          <Button onClick={handleSave} isLoading={saving || loading} icon={<Save className="w-4 h-4" />} disabled={!localConfig}>
            Commit Changes
          </Button>
        </div>
      </div>

      {status && (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm animate-in fade-in slide-in-from-top-2 duration-300 ${
          status.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-red-50 text-red-700 border border-red-100'
        }`}>
          <AlertCircle className="w-5 h-5" />
          <span className="font-medium">{status.message}</span>
        </div>
      )}

      {localConfig && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Section 1: Pipeline Steps */}
          <TagListEditor 
            label="Execution Sequence" 
            items={localConfig.steps || []} 
            onChange={(steps) => handleUpdate({ steps })}
            placeholder="e.g. extractor, classifier..."
          />

          {/* Section 2: Summary / Source Info */}
          <div className="bg-slate-900 text-white p-6 rounded-xl shadow-lg flex flex-col justify-between">
             <div>
                <div className="flex items-center gap-2 mb-4 text-brand-400">
                  <Database className="w-5 h-5" />
                  <span className="text-xs font-bold uppercase tracking-widest">Runtime Context</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {/* Using any cast to access summary properties correctly */}
                  {Object.entries((localConfig as any).summary || {}).slice(0, 4).map(([k, v]) => (
                    <div key={k}>
                      <p className="text-[10px] text-slate-400 uppercase">{k}</p>
                      <p className="text-lg font-mono font-bold text-white truncate">{String(v)}</p>
                    </div>
                  ))}
                </div>
             </div>
             <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
                {/* Accessing source property via any cast to bypass property existence check */}
                <span className={`w-2 h-2 rounded-full ${(localConfig as any).source === 'db' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                <span>Source: {(localConfig as any).source === 'db' ? 'PostgreSQL Production' : 'Local File Fallback'}</span>
             </div>
          </div>

          {/* Section 3: Keyword Manager (Full Width) */}
          {/* Accessing keywords_tech property via any cast */}
          <KeywordCategoryEditor 
            data={(localConfig as any).keywords_tech || {}} 
            onChange={(keywords_tech) => handleUpdate({ keywords_tech })} 
          />

          {/* Section 4: Functional Objects */}
          {/* Using type assertions to access configuration objects that may be reported as missing on PipelineConfig */}
          <KeyValueEditor 
            label="Semantic Templates" 
            data={(localConfig as any).semantic_templates || {}} 
            onChange={(semantic_templates) => handleUpdate({ semantic_templates })} 
            icon={<Hash className="w-4 h-4 text-brand-500" />}
          />
          
          <KeyValueEditor 
            label="Line Filtering Logic" 
            data={(localConfig as any).line_filter || {}} 
            onChange={(line_filter) => handleUpdate({ line_filter })} 
            icon={<ListTree className="w-4 h-4 text-orange-500" />}
          />

          <KeyValueEditor 
            label="Index Generation Rules" 
            data={(localConfig as any).index_rules || {}} 
            onChange={(index_rules) => handleUpdate({ index_rules })} 
          />

          <KeyValueEditor 
            label="Foreigner Classifier Settings" 
            data={(localConfig as any).classifier_foreigner || {}} 
            onChange={(classifier_foreigner) => handleUpdate({ classifier_foreigner })} 
            icon={<Server className="w-4 h-4 text-purple-500" />}
          />
        </div>
      )}
    </div>
  );
};
