import { 
  PipelineConfig, 
  UploadResponseItem, 
  DeleteResponse, 
  RunResponse, 
  TechInsightRequest, 
  TechInsightResponse 
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '';

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
    files.forEach(file => {
      formData.append('files[]', file);
    });

    const res = await fetch(`${API_BASE}/pipeline/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<UploadResponseItem[]>(res);
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

  // Helper to list files - inferred requirement as standard CRUD needs a list
  // If backend doesn't support GET /pipeline/files, we might need to track locally
  // For now, we will assume a GET endpoint exists or return empty to handle gracefully
  listFiles: async (): Promise<UploadResponseItem[]> => {
    try {
      const res = await fetch(`${API_BASE}/pipeline/files`); // Hypothesized endpoint
      if (res.ok) return res.json();
      return [];
    } catch (e) {
      console.warn("Could not list files, might not be supported by API");
      return [];
    }
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
