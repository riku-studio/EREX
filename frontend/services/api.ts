import { 
  PipelineConfig, 
  UploadResponseItem, 
  DeleteResponse, 
  RunResponse, 
  TechInsightRequest, 
  TechInsightResponse,
  PipelineConfigUpdatePayload 
} from '../types';

const API_BASE =
  import.meta.env.VITE_API_BASE !== undefined
    ? import.meta.env.VITE_API_BASE
    : '';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API Error ${response.status}: ${text}`);
  }
  return response.json();
}

export const api = {
  fetchConfig: async (): Promise<PipelineConfig> => {
    const res = await fetch(`${API_BASE}/pipeline/config`);
    return handleResponse<PipelineConfig>(res);
  },

  uploadFiles: async (files: File[]): Promise<UploadResponseItem[]> => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const res = await fetch(`${API_BASE}/pipeline/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<UploadResponseItem[]>(res);
  },

  updateConfig: async (payload: PipelineConfigUpdatePayload): Promise<PipelineConfig> => {
    const res = await fetch(`${API_BASE}/pipeline/config`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<PipelineConfig>(res);
  },

  deleteFiles: async (filenames: string[]): Promise<DeleteResponse> => {
    const res = await fetch(`${API_BASE}/pipeline/files`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(filenames),
    });
    return handleResponse<DeleteResponse>(res);
  },

  listFiles: async (): Promise<UploadResponseItem[]> => {
    const res = await fetch(`${API_BASE}/pipeline/files`);
    return handleResponse<UploadResponseItem[]>(res);
  },

  runPipeline: async (): Promise<RunResponse> => {
    const res = await fetch(`${API_BASE}/pipeline/run`, {
      method: 'POST',
    });
    return handleResponse<RunResponse>(res);
  },

  getTechInsight: async (payload: TechInsightRequest): Promise<TechInsightResponse> => {
    const res = await fetch(`${API_BASE}/pipeline/tech-insight`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<TechInsightResponse>(res);
  }
};
