"use client";

import { useEffect, useRef, useState } from "react";
import {
  REFUSE,
  SUGGESTIONS,
  buildDuo,
  moodRes,
  resolveResponse,
} from "@/lib/cinephile/data";
import { MODES } from "@/lib/cinephile/constants";
import type {
  AppConfig,
  ChatMessage,
  ChatResponse,
  Mood,
  Movie,
} from "@/lib/cinephile/types";
import {
  BigCard,
  Carousel,
  Compare,
  DuoResult,
  Icon,
  ReasoningPanel,
} from "./movie-ui";
import {
  Composer,
  EmptyState,
  Header,
  Loading,
  UsernameGate,
} from "./chrome";

function AssistantBody({
  res,
  onPick,
  onRetry,
}: {
  res: ChatResponse;
  onPick: (text: string) => void;
  onRetry: () => void;
}) {
  const {
    kind,
    layout,
    text,
    movies,
    reasoning,
    availability,
    compareNote,
    refuseChips,
    errCode,
    tasteA,
    tasteB,
    duoPicks,
  } = res;

  if (kind === "error") {
    return (
      <div className="bubble error">
        <div style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
          <Icon
            name="alert"
            style={{
              width: 18,
              height: 18,
              color: "var(--danger)",
              flexShrink: 0,
              marginTop: 2,
            }}
          />
          <div>
            <div style={{ fontWeight: 700, marginBottom: 4, color: "#fff" }}>
              Đã có lỗi xảy ra
            </div>
            <div style={{ fontSize: 14, color: "var(--text-mut)" }}>{text}</div>
            {errCode && (
              <div
                style={{
                  fontSize: 11.5,
                  color: "var(--text-faint)",
                  marginTop: 7,
                  fontFamily: "ui-monospace, monospace",
                }}
              >
                {errCode}
              </div>
            )}
            <div className="err-actions">
              <button type="button" className="btn-retry" onClick={onRetry}>
                <Icon name="retry" /> Thử lại
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (kind === "refuse") {
    return (
      <>
        <div className="bubble refuse" dangerouslySetInnerHTML={{ __html: text }} />
        <div className="chips" style={{ justifyContent: "flex-start" }}>
          {refuseChips?.map((c, i) => (
            <button type="button" className="chip" key={i} onClick={() => onPick(c)}>
              <span className="ci">
                <Icon name="sparkle" />
              </span>
              {c}
            </button>
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <div className="bubble ai" dangerouslySetInnerHTML={{ __html: text }} />
      {layout === "carousel" && movies && <Carousel movies={movies} />}
      {layout === "big" && movies && (
        <BigCard m={movies[0]} availability={availability} />
      )}
      {layout === "compare" && movies && (
        <Compare movies={movies} note={compareNote} />
      )}
      {layout === "duo" && duoPicks && tasteA && tasteB && (
        <DuoResult tasteA={tasteA} tasteB={tasteB} picks={duoPicks} />
      )}
      {reasoning && reasoning.length > 0 && <ReasoningPanel steps={reasoning} />}
    </>
  );
}

function MessageRow({
  msg,
  onPick,
  onRetry,
}: {
  msg: ChatMessage;
  onPick: (text: string) => void;
  onRetry: () => void;
}) {
  if (msg.role === "user") {
    return (
      <div className="msg user">
        <div className="avatar me">Bạn</div>
        <div className="bubble-wrap">
          <div className="bubble me">{msg.text}</div>
        </div>
      </div>
    );
  }
  return (
    <div className="msg ai">
      <div className="avatar ai">
        <Icon name="clapper" style={{ color: "#fff" }} />
      </div>
      <div className="bubble-wrap">
        <AssistantBody res={msg.res} onPick={onPick} onRetry={onRetry} />
      </div>
    </div>
  );
}

async function callRealApi({
  message,
  cfg,
  history,
}: {
  message: string;
  cfg: AppConfig;
  history: ChatMessage[];
}): Promise<ChatResponse> {
  const resp = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      mode: cfg.mode,
      model: cfg.model,
      max_steps: cfg.maxSteps,
      history: history.map((h) => ({
        role: h.role,
        content: h.role === "user" ? h.text : "",
      })),
    }),
  });
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  const data = await resp.json();

  const norm = (mv: Movie & { poster_url?: string }): Movie => {
    let h = 0;
    const t = mv.title || "";
    for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) % 360;
    return {
      ...mv,
      h1: h,
      h2: (h + 38) % 360,
      rating: mv.rating ?? 0,
      genres: mv.genres || [],
    };
  };

  if (data.refused) return REFUSE;
  const movies = (data.movies || []).map(norm);
  return {
    kind: "normal",
    layout: !movies.length ? "none" : movies.length === 1 ? "big" : "carousel",
    text: "<p>" + (data.answer || "").replace(/\n+/g, "</p><p>") + "</p>",
    movies,
    reasoning: data.reasoning || [],
  };
}

export function CinephileApp() {
  const USE_REAL_API = false;
  const cfg: AppConfig = {
    mode: "react2",
    model: "openai/gpt-4o-mini",
    maxSteps: 5,
    realApi: USE_REAL_API,
  };

  const [user, setUser] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem("cinephile.user");
    } catch {
      return null;
    }
  });
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastUserRef = useRef("");

  const scrollDown = () => {
    requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    });
  };
  useEffect(scrollDown, [msgs, loading]);

  async function send(text?: string, forced?: ChatResponse) {
    const q = (text ?? draft).trim();
    if (!q || loading) return;
    lastUserRef.current = q;
    setDraft("");
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setLoading(true);

    const history = msgs;
    try {
      let res: ChatResponse;
      if (cfg.realApi) {
        res = await callRealApi({ message: q, cfg, history });
      } else {
        const delay = MODES.find((m) => m.id === cfg.mode)?.react ? 2600 : 900;
        await new Promise((r) => setTimeout(r, delay));
        res = forced || resolveResponse(q);
      }
      setMsgs((m) => [...m, { role: "ai", res }]);
    } catch (err) {
      setMsgs((m) => [
        ...m,
        {
          role: "ai",
          res: {
            kind: "error",
            layout: "none",
            text: "Không kết nối được tới máy chủ agent (POST /api/chat). Kiểm tra backend FastAPI rồi thử lại.",
            errCode: String(err instanceof Error ? err.message : err),
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function pickMood(m: Mood) {
    send(m.prompt, moodRes(m));
  }
  function pickDuo(a: string, b: string) {
    send(
      `Đôi mình muốn xem chung — một người thích ${a.trim()}, một người thích ${b.trim()}.`,
      buildDuo(a, b),
    );
  }

  function retry() {
    if (lastUserRef.current) send(lastUserRef.current);
  }

  function newChat() {
    setMsgs([]);
    setDraft("");
    lastUserRef.current = "";
  }

  function signOut() {
    try {
      localStorage.removeItem("cinephile.user");
    } catch {
      /* ignore */
    }
    setUser(null);
    newChat();
  }

  if (!user) return <UsernameGate onDone={(u) => setUser(u)} />;

  return (
    <div className="app">
      <Header
        showNew={msgs.length > 0}
        onNewChat={newChat}
        user={user}
        onSignOut={signOut}
      />

      <div className="chat-scroll" ref={scrollRef}>
        {msgs.length === 0 && !loading ? (
          <EmptyState
            onPick={(t) => send(t)}
            onMood={pickMood}
            onDuo={pickDuo}
            user={user}
          />
        ) : (
          <div className="chat-inner">
            {msgs.map((m, i) => (
              <MessageRow key={i} msg={m} onPick={(t) => send(t)} onRetry={retry} />
            ))}
            {loading && <Loading mode={cfg.mode} />}
          </div>
        )}
      </div>

      {msgs.length > 0 && (
        <div className="quick-row no-scrollbar">
          {SUGGESTIONS.map((s, i) => (
            <button
              type="button"
              className="qchip"
              key={i}
              onClick={() => send(s.text)}
              disabled={loading}
            >
              {s.text}
            </button>
          ))}
        </div>
      )}

      <div className="composer-zone">
        <Composer
          value={draft}
          onChange={setDraft}
          onSend={() => send()}
          disabled={loading}
        />
      </div>
    </div>
  );
}
