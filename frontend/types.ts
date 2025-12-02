export interface PipelineConfig {
  summary: Record<string, any>;
  steps: string[];
  line_filter: Record<string, any>;
  semantic_templates: Record<string, any>;
  keywords_tech: Record<string, any>;
  index_rules: Record<string, any>;
  classifier_foreigner: Record<string, any>;
  source?: string;
}

export interface PipelineConfigUpdatePayload {
  steps: string[];
  line_filter: Record<string, any>;
  semantic_templates: Record<string, any>;
  keywords_tech: Record<string, any>;
  index_rules: Record<string, any>;
  classifier_foreigner: Record<string, any>;
}

export interface UploadResponseItem {
  filename: string;
  size: number;
}

export interface DeleteResponse {
  deleted: number;
  skipped: number;
}

export interface SemanticResult {
  text: string;
  score: number;
  start_line: number;
  end_line: number;
  matched: boolean;
  line_scores: number[];
}

export interface KeywordStat {
  keyword: string;
  count: number;
  ratio: number;
}

export interface ClassStat {
  count: number;
  ratio: number;
}

export interface Aggregation {
  block_count: number;
  keyword_summary: Record<string, KeywordStat[]>; // Category -> Stats
  class_summary: Record<string, ClassStat>; // ClassName -> Stats
}

export interface MailResult {
  source_path: string;
  subject: string;
  semantic: SemanticResult | null;
  aggregation: Aggregation;
}

export interface RunSummary {
  message_count: number;
  block_count: number;
  keyword_summary: Record<string, KeywordStat[]>;
  class_summary: Record<string, ClassStat>;
}

export interface RunResponse {
  results: MailResult[];
  summary: RunSummary;
}

export interface TechInsightRequest {
  keyword: string;
  count: number;
  ratio: number;
  category?: string;
}

export interface TechInsightResponse {
  keyword: string;
  insight: string;
}

// UI specific types
export type TabView = 'dashboard' | 'files' | 'config';
