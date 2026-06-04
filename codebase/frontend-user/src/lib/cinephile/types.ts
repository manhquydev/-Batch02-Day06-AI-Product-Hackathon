export type Movie = {
  id?: number;
  title: string;
  year: number;
  rating: number;
  genres: string[];
  netflix?: boolean;
  overview?: string;
  h1: number;
  h2: number;
};

export type ReasoningStep = {
  thought: string;
  action: string;
  observe: string;
};

export type WhereToWatchData = {
  netflix?: boolean;
  flatrate?: string[];
  rent?: string[];
  buy?: string[];
  soon?: string[];
};

export type Availability = {
  netflix: boolean;
  where?: WhereToWatchData;
  note?: string;
};

export type DuoPick = { m: Movie; why: string };

export type ChatResponse = {
  kind: "normal" | "refuse" | "error";
  layout: "carousel" | "big" | "compare" | "none" | "duo";
  text: string;
  movies?: Movie[];
  reasoning?: ReasoningStep[];
  availability?: Availability;
  compareNote?: string;
  refuseChips?: string[];
  errCode?: string;
  tasteA?: string;
  tasteB?: string;
  duoPicks?: DuoPick[];
  plain?: string;
};

export type UserMessage = { role: "user"; text: string };
export type AiMessage = { role: "ai"; res: ChatResponse };
export type ChatMessage = UserMessage | AiMessage;

export type AgentMode = {
  id: string;
  name: string;
  tag?: string;
  desc: string;
  react: boolean;
};

export type Mood = {
  id: string;
  label: string;
  sub: string;
  icon: string;
  h: number;
  prompt: string;
  movies: Movie[];
};

export type Suggestion = { icon: string; text: string };

export type AppConfig = {
  mode: string;
  model: string;
  maxSteps: number;
  realApi: boolean;
};
