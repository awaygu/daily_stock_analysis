import type { StrategyInfo, RetrievalResult } from '../types/strategy';

export interface StrategyUploadResponse {
  strategy_id: string;
  name: string;
  chunk_count: number;
  message: string;
}

export interface StrategyListResponse {
  strategies: StrategyInfo[];
  total: number;
}

export interface RetrievalResponse {
  query: string;
  results: RetrievalResult[];
  strategy_id: string | null;
}

export interface UploadStrategyParams {
  file: File;
  name?: string;
  description?: string;
}

export async function uploadStrategy(params: UploadStrategyParams): Promise<StrategyUploadResponse> {
  const formData = new FormData();
  formData.append('file', params.file);
  if (params.name) {
    formData.append('name', params.name);
  }
  if (params.description) {
    formData.append('description', params.description);
  }

  const response = await fetch('/api/v1/rag/strategies/upload', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '策略上传失败');
  }

  return response.json();
}

export async function listStrategies(): Promise<StrategyListResponse> {
  const response = await fetch('/api/v1/rag/strategies');
  if (!response.ok) {
    throw new Error('获取策略列表失败');
  }
  return response.json();
}

export async function getStrategy(strategyId: string): Promise<StrategyInfo> {
  const response = await fetch(`/api/v1/rag/strategies/${strategyId}`);
  if (!response.ok) {
    throw new Error('获取策略详情失败');
  }
  return response.json();
}

export async function deleteStrategy(strategyId: string): Promise<void> {
  const response = await fetch(`/api/v1/rag/strategies/${strategyId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('删除策略失败');
  }
}

export async function retrieveStrategy(
  query: string,
  topK: number = 5,
  strategyId?: string
): Promise<RetrievalResponse> {
  const params = new URLSearchParams({ query: query, top_k: String(topK) });
  if (strategyId) {
    params.append('strategy_id', strategyId);
  }

  const response = await fetch(`/api/v1/rag/retrieve?${params}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('检索策略失败');
  }

  return response.json();
}