export type TraceStep = {
  step: number;
  thought: string | null;
  action: string | null;
  observation: string | null;
  raw: string;
};

export type Movie = {
  id?: number;
  title?: string;
  [key: string]: unknown;
};

export type ChatResponse = {
  answer: string;
  trace: TraceStep[];
  steps: number;
  latency_ms: number;
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  mode: string;
  movies: Movie[];
};

export type CompareResult = {
  ok: boolean;
  error?: string;
  answer: string;
  trace?: TraceStep[];
  steps?: number;
  latency_ms?: number;
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  mode?: string;
  movies: Movie[];
};

export type CompareResponse = {
  results: Record<string, CompareResult>;
};