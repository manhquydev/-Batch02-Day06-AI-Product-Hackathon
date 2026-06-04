import type { ChatResponse, CompareResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function fetchModels(): Promise<{ models: string[] }> {
  return apiFetch("/api/models");
}

export type ChatParams = {
  message: string;
  mode: string;
  provider: string;
  model: string;
  max_steps: number;
};

export function runChat(params: ChatParams): Promise<ChatResponse> {
  return apiFetch("/api/chat", { method: "POST", body: JSON.stringify(params) });
}

export type CompareParams = {
  query: string;
  models: string[];
  mode: string;
  max_steps: number;
};

export function runCompare(params: CompareParams): Promise<CompareResponse> {
  return apiFetch("/api/compare", { method: "POST", body: JSON.stringify(params) });
}
