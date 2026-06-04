import type { AgentMode } from "./types";

export const MODES: (AgentMode & { backendMode: string })[] = [
  {
    id: "react2",
    name: "ReAct Agent v2",
    backendMode: "ReAct Agent v2",
    tag: "Mặc định",
    desc: "Vòng lặp suy luận + công cụ TMDB.",
    react: true,
  },
  {
    id: "react1",
    name: "ReAct Agent v1",
    backendMode: "ReAct Agent v1",
    desc: "Phiên bản agent đời đầu.",
    react: true,
  },
  {
    id: "chatbot",
    name: "Chatbot baseline",
    backendMode: "Chatbot Baseline",
    desc: "Mô hình thuần, không gọi công cụ.",
    react: false,
  },
];

const BACKEND_MODE_BY_ID = Object.fromEntries(
  MODES.map((m) => [m.id, m.backendMode]),
) as Record<string, string>;

export function modeIdToBackend(modeId: string): string {
  return BACKEND_MODE_BY_ID[modeId] ?? "ReAct Agent v2";
}
