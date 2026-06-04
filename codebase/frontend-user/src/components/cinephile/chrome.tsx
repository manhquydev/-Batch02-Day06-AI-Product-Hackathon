"use client";

import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { MOODS, SUGGESTIONS } from "@/lib/cinephile/data";
import { MODES } from "@/lib/cinephile/constants";
import type { Mood } from "@/lib/cinephile/types";
import { Icon } from "./movie-ui";

export function Header({
  onNewChat,
  showNew,
  user,
  onSignOut,
}: {
  onNewChat: () => void;
  showNew: boolean;
  user: string;
  onSignOut: () => void;
}) {
  return (
    <header className="hdr">
      <div className="brand">
        <div className="brand-mark">
          <Icon name="clapper" style={{ color: "#fff" }} />
        </div>
        <div className="brand-text">
          <div className="brand-name">Cinephile</div>
          <div className="brand-sub">AI gợi ý phim · dữ liệu TMDB</div>
        </div>
      </div>
      <div className="hdr-spacer" />
      {showNew && (
        <button
          type="button"
          className="icon-btn"
          onClick={onNewChat}
          aria-label="Trò chuyện mới"
          title="Trò chuyện mới"
        >
          <Icon name="newchat" />
        </button>
      )}
      {user && (
        <button
          type="button"
          className="user-chip"
          onClick={onSignOut}
          title="Đổi người dùng / đăng xuất"
        >
          <span className="user-av">{user[0].toUpperCase()}</span>
          <span className="user-name">{user}</span>
        </button>
      )}
    </header>
  );
}

export function UsernameGate({ onDone }: { onDone: (u: string) => void }) {
  const [val, setVal] = useState("");
  const [err, setErr] = useState("");
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);

  const taken = () => {
    try {
      return JSON.parse(localStorage.getItem("cinephile.users") || "[]") as string[];
    } catch {
      return [];
    }
  };
  const submit = () => {
    const u = val.trim();
    if (u.length < 3) return setErr("Tên cần ít nhất 3 ký tự.");
    if (u.length > 20) return setErr("Tên tối đa 20 ký tự.");
    if (!/^[a-zA-Z0-9_.]+$/.test(u))
      return setErr("Chỉ dùng chữ, số, dấu . hoặc _ (không khoảng trắng).");
    const list = taken();
    if (list.some((x) => x.toLowerCase() === u.toLowerCase()))
      return setErr("Tên này đã có người dùng. Thử tên khác nhé.");
    localStorage.setItem("cinephile.users", JSON.stringify([...list, u]));
    localStorage.setItem("cinephile.user", u);
    onDone(u);
  };

  return (
    <div className="gate">
      <div className="gate-card">
        <div className="empty-mark" style={{ margin: "0 auto 22px" }}>
          <Icon name="clapper" style={{ color: "#fff" }} />
        </div>
        <div className="gate-kicker">Cinephile</div>
        <h1 className="gate-title">
          Trước khi vào rạp,
          <br />
          <span className="accent">đặt tên</span> cho mình nhé
        </h1>
        <p className="gate-sub">
          Chọn một tên người dùng <strong>duy nhất</strong>. Mình dùng nó để ghi nhớ gu phim và
          watchlist của bạn.
        </p>
        <div className={"gate-field" + (err ? " has-err" : "")}>
          <span className="gate-at">@</span>
          <input
            ref={ref}
            value={val}
            placeholder="ten_cua_ban"
            maxLength={20}
            onChange={(e) => {
              setVal(e.target.value);
              setErr("");
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />
        </div>
        {err && (
          <div className="gate-err">
            <Icon name="alert" style={{ width: 13, height: 13 }} /> {err}
          </div>
        )}
        <button type="button" className="gate-btn" onClick={submit} disabled={!val.trim()}>
          Bắt đầu xem phim <Icon name="chevright" style={{ width: 16, height: 16 }} />
        </button>
        <div className="gate-foot">Chỉ lưu trên thiết bị này · không cần mật khẩu</div>
      </div>
    </div>
  );
}

function MoodPicker({ onPick }: { onPick: (m: Mood) => void }) {
  return (
    <div className="mood-grid">
      {MOODS.map((m) => (
        <button
          type="button"
          className="mood-tile"
          key={m.id}
          onClick={() => onPick(m)}
          style={{ "--mh": m.h } as CSSProperties}
        >
          <span className="mood-ic">
            <Icon name={m.icon} />
          </span>
          <span className="mood-label">{m.label}</span>
          <span className="mood-sub">{m.sub}</span>
        </button>
      ))}
    </div>
  );
}

function DuoForm({ onSubmit }: { onSubmit: (a: string, b: string) => void }) {
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const go = () => {
    if (a.trim() && b.trim()) onSubmit(a, b);
  };
  return (
    <div className="duo-card">
      <div className="duo-card-head">
        <span className="duo-ic">
          <Icon name="duo" />
        </span>{" "}
        Đôi mình xem gì?
        <span className="duo-card-sub">Nhập gu của hai người, mình tìm phim chung</span>
      </div>
      <div className="duo-inputs">
        <input
          value={a}
          onChange={(e) => setA(e.target.value)}
          placeholder="Gu của bạn (vd: kinh dị)"
          onKeyDown={(e) => e.key === "Enter" && go()}
        />
        <span className="duo-amp">
          <Icon name="duo" style={{ width: 14, height: 14 }} />
        </span>
        <input
          value={b}
          onChange={(e) => setB(e.target.value)}
          placeholder="Gu người kia (vd: rom-com)"
          onKeyDown={(e) => e.key === "Enter" && go()}
        />
        <button type="button" className="duo-go" disabled={!a.trim() || !b.trim()} onClick={go}>
          Tìm phim chung
        </button>
      </div>
    </div>
  );
}

export function EmptyState({
  onPick,
  onMood,
  onDuo,
  user,
}: {
  onPick: (text: string) => void;
  onMood: (m: Mood) => void;
  onDuo: (a: string, b: string) => void;
  user: string;
}) {
  return (
    <div className="empty tall">
      <div className="empty-mark">
        <Icon name="clapper" style={{ color: "#fff" }} />
      </div>
      {user && (
        <div className="empty-greet">
          Chào <strong>@{user}</strong>
        </div>
      )}
      <h1>
        Tối nay <span className="accent">xem gì?</span>
      </h1>
      <p>
        Hỏi mình bằng tiếng Việt — theo tâm trạng, thể loại, nền tảng, hay phim bạn từng thích.
        Mình tra dữ liệu TMDB thật rồi gợi ý kèm poster, rating và nơi xem.
      </p>

      <div className="empty-section">
        <div className="empty-section-h">Chọn theo tâm trạng</div>
        <MoodPicker onPick={onMood} />
      </div>

      <div className="empty-section">
        <DuoForm onSubmit={onDuo} />
      </div>

      <div className="empty-section">
        <div className="empty-section-h">Hoặc thử hỏi</div>
        <div className="chips">
          {SUGGESTIONS.map((s, i) => (
            <button type="button" className="chip" key={i} onClick={() => onPick(s.text)}>
              <span className="ci">
                <Icon name={s.icon} />
              </span>
              {s.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

const LOAD_STEPS = [
  "Phân tích yêu cầu của bạn",
  "Gọi công cụ TMDB",
  "Đọc & lọc kết quả",
  "Tổng hợp câu trả lời",
];

export function Loading({ mode }: { mode: string }) {
  const [step, setStep] = useState(0);
  const isReact = MODES.find((m) => m.id === mode)?.react;
  const steps = isReact ? LOAD_STEPS : ["Đang soạn câu trả lời"];
  useEffect(() => {
    if (!isReact) return;
    const t = setInterval(
      () => setStep((s) => Math.min(s + 1, steps.length - 1)),
      850,
    );
    return () => clearInterval(t);
  }, [isReact, steps.length]);
  return (
    <div className="msg ai">
      <div className="avatar ai">
        <Icon name="clapper" style={{ color: "#fff" }} />
      </div>
      <div className="bubble-wrap">
        <div className="bubble ai" style={{ width: "100%", maxWidth: "100%" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 9,
              marginBottom: isReact ? 13 : 0,
              fontWeight: 600,
              fontSize: 13.5,
            }}
          >
            <span className="thinking-dots">
              <i />
              <i />
              <i />
            </span>
            {isReact ? "Agent đang suy luận…" : "Đang trả lời…"}
          </div>
          {isReact && (
            <div className="loading-steps">
              {steps.map((s, i) => (
                <div
                  key={i}
                  className={
                    "lstep " + (i < step ? "done" : i === step ? "active" : "pending")
                  }
                >
                  <span className="ldot">{i < step && <Icon name="check" />}</span>
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>
        {isReact && (
          <div className="skel-row">
            {[0, 1, 2, 3, 4].map((i) => (
              <div className="skel-card" key={i}>
                <div className="skel-poster" />
                <div className="skel-line" />
                <div className="skel-line sm" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function Composer({
  value,
  onChange,
  onSend,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
}) {
  const ta = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (!ta.current) return;
    ta.current.style.height = "auto";
    ta.current.style.height = Math.min(ta.current.scrollHeight, 140) + "px";
  }, [value]);
  const key = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSend();
    }
  };
  return (
    <div className="composer">
      <div className="composer-box">
        <textarea
          ref={ta}
          rows={1}
          value={value}
          placeholder="Hỏi mình về phim… (vd: phim trinh thám hay trên Netflix)"
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={key}
          disabled={disabled}
        />
        <button
          type="button"
          className="send-btn"
          disabled={!value.trim() || disabled}
          onClick={onSend}
          aria-label="Gửi"
        >
          <Icon name="send" />
        </button>
      </div>
      <div className="composer-hint">
        <kbd>Enter</kbd> để gửi · <kbd>Shift</kbd>+<kbd>Enter</kbd> xuống dòng
      </div>
    </div>
  );
}
