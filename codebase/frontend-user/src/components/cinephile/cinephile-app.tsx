"use client";

import { useEffect, useRef, useState } from "react";
import { buildDuo, moodRes, resolveResponse } from "@/lib/cinephile/data";
import { mockFollowUps } from "@/lib/cinephile/follow-ups";
import {
  mapBackendToChatResponse,
  parseModelKey,
  runChat,
  USE_REAL_API,
} from "@/lib/api";
import { newSessionId } from "@/lib/cinephile/session";
import { MODES } from "@/lib/cinephile/constants";
import type {
  AppConfig,
  ChatMessage,
  ChatResponse,
  FollowUpChip,
  Mood,
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

function FollowUpChips({
  chips,
  onPick,
  disabled,
}: {
  chips: FollowUpChip[];
  onPick: (text: string) => void;
  disabled?: boolean;
}) {
  if (!chips.length) return null;
  const hasKinds = chips.some((c) => c.kind);
  const detailChips = hasKinds ? chips.filter((c) => c.kind === "detail") : [];
  const continueChips = hasKinds
    ? chips.filter((c) => c.kind === "continue")
    : chips.filter((c) => c.kind !== "explore");
  const exploreChips = hasKinds ? chips.filter((c) => c.kind === "explore") : [];

  const renderGroup = (label: string, items: FollowUpChip[], className: string) => {
    if (!items.length) return null;
    return (
      <div className={`follow-up-group ${className}`}>
        <div className="follow-up-label">{label}</div>
        <div className="follow-up-chips">
          {items.map((c, i) => (
            <button
              type="button"
              className="chip follow-chip"
              key={`${className}-${i}`}
              disabled={disabled}
              onClick={() => onPick(c.text)}
            >
              <span className="ci">
                <Icon
                  name={
                    className === "explore"
                      ? "sparkle"
                      : className === "detail"
                        ? "clapper"
                        : "layers"
                  }
                />
              </span>
              {c.text}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="follow-up-row">
      {renderGroup("Tìm hiểu thêm", detailChips, "detail")}
      {renderGroup("Tiếp tục chủ đề", continueChips, "continue")}
      {renderGroup("Thử chủ đề khác", exploreChips, "explore")}
    </div>
  );
}

function AssistantBody({
  res,
  onPick,
  onRetry,
  chipsDisabled,
}: {
  res: ChatResponse;
  onPick: (text: string) => void;
  onRetry: () => void;
  chipsDisabled?: boolean;
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
    followUps,
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
    const chips: FollowUpChip[] =
      followUps ??
      refuseChips?.map((t) => ({ text: t, kind: "explore" as const })) ??
      [];
    return (
      <>
        <div className="bubble refuse" dangerouslySetInnerHTML={{ __html: text }} />
        <FollowUpChips chips={chips} onPick={onPick} disabled={chipsDisabled} />
      </>
    );
  }

  const chips =
    followUps ??
    (movies?.length
      ? [
          {
            text: `Cho tôi thêm phim cùng thể loại`,
            kind: "continue" as const,
          },
        ]
      : []);

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
      <FollowUpChips chips={chips} onPick={onPick} disabled={chipsDisabled} />
    </>
  );
}

function MessageRow({
  msg,
  onPick,
  onRetry,
  chipsDisabled,
}: {
  msg: ChatMessage;
  onPick: (text: string) => void;
  onRetry: () => void;
  chipsDisabled?: boolean;
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
        <AssistantBody
          res={msg.res}
          onPick={onPick}
          onRetry={onRetry}
          chipsDisabled={chipsDisabled}
        />
      </div>
    </div>
  );
}

const DEFAULT_MODEL_KEY =
  process.env.NEXT_PUBLIC_DEFAULT_MODEL ?? "openai/gpt-4o-mini";

const DEFAULT_MAX_STEPS = Math.min(
  12,
  Math.max(2, Number(process.env.NEXT_PUBLIC_MAX_STEPS || 8) || 8),
);

export function CinephileApp() {
  const { provider, model } = parseModelKey(DEFAULT_MODEL_KEY);
  const cfg: AppConfig = {
    mode: "react2",
    model,
    provider,
    maxSteps: DEFAULT_MAX_STEPS,
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
  const [sessionId, setSessionId] = useState(() => newSessionId());
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastUserRef = useRef("");
  const sessionIdRef = useRef(sessionId);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

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

    try {
      let res: ChatResponse;
      if (cfg.realApi) {
        const data = await runChat({
          message: q,
          session_id: sessionIdRef.current,
          modeId: cfg.mode,
          provider: cfg.provider,
          model: cfg.model,
          max_steps: cfg.maxSteps,
        });
        if (data.session_id && data.session_id !== sessionIdRef.current) {
          setSessionId(data.session_id);
        }
        res = mapBackendToChatResponse(data);
      } else {
        const delay = MODES.find((m) => m.id === cfg.mode)?.react ? 2600 : 900;
        await new Promise((r) => setTimeout(r, delay));
        const base = forced || resolveResponse(q);
        res = base.followUps?.length
          ? base
          : { ...base, followUps: mockFollowUps(q, base) };
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
    send(m.prompt, cfg.realApi ? undefined : moodRes(m));
  }

  /** Prompt gửi backend — bắt buộc có intent phim để không bị domain_guard chặn. */
  function duoApiPrompt(a: string, b: string): string {
    const ta = a.trim();
    const tb = b.trim();
    return (
      `Gợi ý phim để hai người xem chung tối nay. ` +
      `Một người thích ${ta}, một người thích ${tb}. ` +
      `Tìm 3–4 phim cân bằng gu của cả hai, ưu tiên phim dễ xem ở Việt Nam.`
    );
  }

  function pickDuo(a: string, b: string) {
    const ta = a.trim();
    const tb = b.trim();
    if (cfg.realApi) {
      send(duoApiPrompt(ta, tb));
      return;
    }
    send(
      `Đôi mình muốn xem chung — một người thích ${ta}, một người thích ${tb}.`,
      buildDuo(ta, tb),
    );
  }

  function retry() {
    if (lastUserRef.current) send(lastUserRef.current);
  }

  function newChat() {
    setMsgs([]);
    setDraft("");
    lastUserRef.current = "";
    const nextId = newSessionId();
    setSessionId(nextId);
    sessionIdRef.current = nextId;
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
              <MessageRow
                key={i}
                msg={m}
                onPick={(t) => send(t)}
                onRetry={retry}
                chipsDisabled={loading}
              />
            ))}
            {loading && <Loading mode={cfg.mode} />}
          </div>
        )}
      </div>

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
