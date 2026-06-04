import type {
  ChatResponse,
  FollowUpKind,
  Movie,
  ReasoningStep,
} from "@/lib/cinephile/types";
import { REFUSE } from "@/lib/cinephile/data";
import { modeIdToBackend } from "@/lib/cinephile/constants";
import { formatAnswerHtml } from "@/lib/cinephile/format-answer";

/**
 * Base URL cho fetch từ trình duyệt.
 * Mặc định "" → gọi cùng origin (Next rewrite → backend), tránh lỗi CORS OPTIONS 400.
 * Chỉ set NEXT_PUBLIC_API_URL khi muốn gọi thẳng backend (phải khớp FRONTEND_USER_URL trên server).
 */
function resolveApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!raw || raw === "/" || raw === "same-origin") return "";
  return raw.replace(/\/$/, "");
}

export const API_BASE = resolveApiBase();

export const USE_REAL_API =
  process.env.NEXT_PUBLIC_USE_REAL_API !== "false";

export type BackendTraceStep = {
  step?: number;
  thought?: string | null;
  action?: string | null;
  observation?: string | null;
  raw?: string;
};

export type BackendChatResponse = {
  answer: string;
  trace?: BackendTraceStep[];
  steps?: number;
  latency_ms?: number;
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  mode?: string;
  movies?: BackendMovie[];
  session_id?: string;
  turn_count?: number;
  summarized?: boolean;
  follow_ups?: { text: string; kind?: "continue" | "explore" | "detail" }[];
};

type BackendMovie = {
  id?: number;
  title?: string;
  year?: number;
  rating?: number;
  genres?: string[] | string;
  netflix?: boolean;
  overview?: string;
  poster_url?: string | null;
  [key: string]: unknown;
};

export type ChatParams = {
  message: string;
  session_id?: string;
  modeId: string;
  provider: string;
  model: string;
  max_steps: number;
};

export function createChatSession(): Promise<{ session_id: string }> {
  return apiFetch("/api/sessions", { method: "POST" });
}

export function resetChatSession(sessionId: string): Promise<{ session_id: string }> {
  return apiFetch(`/api/sessions/${encodeURIComponent(sessionId)}/reset`, {
    method: "POST",
  });
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail =
        typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail ?? body);
    } catch {
      detail = await res.text().catch(() => "");
    }
    throw new Error(`${res.status}: ${detail || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function fetchHealth(): Promise<{
  status: string;
  openai_configured: boolean;
  tmdb_configured: boolean;
}> {
  return apiFetch("/health");
}

export function runChat(params: ChatParams): Promise<BackendChatResponse> {
  const mode = modeIdToBackend(params.modeId);
  return apiFetch("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message: params.message,
      session_id: params.session_id,
      mode,
      provider: params.provider,
      model: params.model,
      max_steps: params.max_steps,
    }),
  });
}

function hueFromTitle(title: string): { h1: number; h2: number } {
  let h = 0;
  for (let i = 0; i < title.length; i++) h = (h * 31 + title.charCodeAt(i)) % 360;
  return { h1: h, h2: (h + 38) % 360 };
}

export function normalizeMovie(raw: BackendMovie): Movie | null {
  const title = (raw.title || "").trim();
  if (!title) return null;
  const { h1, h2 } = hueFromTitle(title);
  const genres = Array.isArray(raw.genres)
    ? raw.genres.map(String)
    : typeof raw.genres === "string"
      ? raw.genres.split(/[,·]/).map((g) => g.trim()).filter(Boolean)
      : [];
  return {
    id: raw.id,
    title,
    year: Number(raw.year) || 0,
    rating: Number(raw.rating) || 0,
    genres: genres.length ? genres : ["Phim"],
    netflix: Boolean(raw.netflix),
    overview: typeof raw.overview === "string" ? raw.overview : undefined,
    poster_url:
      typeof raw.poster_url === "string" && raw.poster_url ? raw.poster_url : undefined,
    h1,
    h2,
  };
}

function traceToReasoning(trace: BackendTraceStep[] | undefined): ReasoningStep[] {
  if (!trace?.length) return [];
  return trace
    .map((s) => ({
      thought: (s.thought || "").trim(),
      action: (s.action || "").trim(),
      observe: (s.observation || "").trim(),
    }))
    .filter((s) => s.thought || s.action || s.observe);
}

export function mapBackendToChatResponse(data: BackendChatResponse): ChatResponse {
  if (data.mode === "domain_guard") {
    const followUps = (data.follow_ups || []).map((c) => ({
      text: c.text.trim(),
      kind: (c.kind === "explore" ? "explore" : "continue") as FollowUpKind,
    }));
    return {
      ...REFUSE,
      text: formatAnswerHtml(data.answer || REFUSE.text),
      followUps: followUps.length
        ? followUps
        : REFUSE.refuseChips?.map((text) => ({ text, kind: "explore" as const })),
    };
  }

  const movies = (data.movies || [])
    .map(normalizeMovie)
    .filter((m): m is Movie => m !== null);

  const reasoning = traceToReasoning(data.trace);
  const compareLike =
    movies.length === 2 &&
    /so sánh|compare/i.test(data.answer || "");

  const followUps = (data.follow_ups || [])
    .filter((c) => c?.text?.trim())
    .map((c) => ({
      text: c.text.trim(),
      kind:
        c.kind === "explore" || c.kind === "continue" || c.kind === "detail"
          ? c.kind
          : undefined,
    }));

  // Don't compact when answer contains reviews — let user read full review text
  const hasReviews = /review|nhận xét|đánh giá của|bình luận|người dùng.*nói|user.*said/i.test(data.answer || "");
  const useCompact = movies.length > 0 && !hasReviews;

  return {
    kind: "normal",
    layout: !movies.length
      ? "none"
      : compareLike
        ? "compare"
        : movies.length === 1
          ? "big"
          : "carousel",
    text: formatAnswerHtml(data.answer || "", { compact: useCompact }),
    movies,
    reasoning: reasoning.length ? reasoning : undefined,
    plain: data.answer,
    followUps: followUps.length ? followUps : undefined,
  };
}

export function parseModelKey(modelKey: string): { provider: string; model: string } {
  const slash = modelKey.indexOf("/");
  if (slash === -1) return { provider: "openai", model: modelKey };
  return {
    provider: modelKey.slice(0, slash),
    model: modelKey.slice(slash + 1),
  };
}
