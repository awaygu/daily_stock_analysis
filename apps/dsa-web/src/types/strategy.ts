export interface StrategyInfo {
  id: string;
  name: string;
  description: string | null;
  file_type: string;
  chunk_count: number;
  created_at: string;
}

export interface RetrievalResult {
  content: string;
  source: string;
  score: number;
  page: number | null;
}