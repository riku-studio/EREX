import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend, LabelList, TooltipProps
} from 'recharts';
import { KeywordStat, ClassStat } from '../types';

interface KeywordChartProps {
  data: KeywordStat[];
  onBarClick: (data: any) => void;
}

const formatPercentage = (value: number | undefined | null) => {
  const safe = Number.isFinite(value ?? NaN) ? (value as number) : 0;
  return `${(safe * 100).toFixed(1)}%`;
};

const KeywordTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload }) => {
  if (!active || !payload?.length) return null;

  const keywordData = payload[0].payload as Partial<KeywordStat>;

  return (
    <div className="rounded-lg bg-white px-3 py-2 shadow-sm border border-slate-200">
      <p className="text-xs font-semibold text-slate-700">{keywordData.keyword}</p>
      <p className="text-xs text-slate-500 mt-1">Count: {keywordData.count}</p>
      <p className="text-xs text-slate-500">Ratio: {formatPercentage(keywordData.ratio)}</p>
    </div>
  );
};

export const KeywordChart: React.FC<KeywordChartProps> = ({ data, onBarClick }) => {
  // Sort by count descending
  const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 10);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart 
        data={sortedData} 
        layout="vertical" 
        margin={{ top: 5, right: 80, left: 40, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
        <XAxis type="number" hide />
        <YAxis 
          dataKey="keyword" 
          type="category" 
          width={100} 
          tick={{fontSize: 12, fill: '#64748b'}} 
        />
        <Tooltip 
          cursor={{fill: '#f1f5f9'}}
          content={<KeywordTooltip />}
        />
        <Bar 
          dataKey="count" 
          fill="#0ea5e9" 
          radius={[0, 4, 4, 0]} 
          barSize={20}
          onClick={(data) => onBarClick(data)}
          className="cursor-pointer hover:opacity-80 transition-opacity"
        >
          <LabelList 
            dataKey="count"
            position="right"
            formatter={(value: number, entry: KeywordStat | undefined) => {
              const ratio = entry?.ratio;
              return `${value} (${formatPercentage(ratio)})`;
            }}
            fill="#0f172a"
            fontSize={12}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

interface ClassChartProps {
  data: Record<string, ClassStat>;
}

const CLASS_COLOR_MAP: Record<string, string> = {
  ok: '#10b981', // green
  ng: '#ef4444', // red
  unknown: '#94a3b8', // gray
};
const FALLBACK_COLORS = ['#0ea5e9', '#f59e0b', '#6366f1', '#8b5cf6'];

export const ClassChart: React.FC<ClassChartProps> = ({ data }) => {
  const chartData = Object.entries(data).map(([key, stat]: [string, ClassStat]) => ({
    name: key.toUpperCase(),
    value: stat.count,
    ratio: stat.ratio
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={CLASS_COLOR_MAP[entry.name.toLowerCase()] || FALLBACK_COLORS[index % FALLBACK_COLORS.length]} 
            />
          ))}
        </Pie>
        <Tooltip 
             contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
        />
        <Legend verticalAlign="bottom" height={36}/>
      </PieChart>
    </ResponsiveContainer>
  );
};
