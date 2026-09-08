import type {
  ExportResponse,
  GeneratePipelineRequest,
  HistoryListResponse,
  PipelineRecord,
} from '../types/pipeline';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
      ...init,
    });
  } catch (error) {
    console.error(error);
    throw new Error(
      `Could not reach backend API at ${API_BASE_URL}. Check the deployment API URL and CORS configuration.`,
    );
  }

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const text = await response.text();
    try {
      const body = JSON.parse(text) as { detail?: string };
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      if (text) {
        message = text;
      }
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  generatePipeline(payload: GeneratePipelineRequest): Promise<PipelineRecord> {
    return request<PipelineRecord>('/api/pipelines/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listHistory(userId: string): Promise<HistoryListResponse> {
    return request<HistoryListResponse>(
      `/api/pipelines/history?user_id=${encodeURIComponent(userId)}`,
    );
  },

  getPipeline(id: string): Promise<PipelineRecord> {
    return request<PipelineRecord>(`/api/pipelines/${id}`);
  },

  deletePipeline(id: string): Promise<void> {
    return request<void>(`/api/pipelines/${id}`, { method: 'DELETE' });
  },

  exportMarkdown(id: string): Promise<ExportResponse> {
    return request<ExportResponse>(`/api/pipelines/${id}/export/markdown`);
  },

  exportJson(id: string): Promise<ExportResponse> {
    return request<ExportResponse>(`/api/pipelines/${id}/export/json`);
  },
};

export function downloadText(filename: string, content: string, contentType: string): void {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
