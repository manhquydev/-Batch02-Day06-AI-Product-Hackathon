import type { AgentMode } from "./types";

export const MODES: AgentMode[] = [
  {
    id: "react2",
    name: "ReAct Agent v2",
    tag: "Mặc định",
    desc: "Vòng lặp suy luận + công cụ TMDB.",
    react: true,
  },
  { id: "react1", name: "ReAct Agent v1", desc: "Phiên bản agent đời đầu.", react: true },
  {
    id: "chatbot",
    name: "Chatbot baseline",
    desc: "Mô hình thuần, không gọi công cụ.",
    react: false,
  },
];
