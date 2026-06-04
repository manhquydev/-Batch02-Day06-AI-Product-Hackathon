"use client";

import { Fragment, useRef, useState, type SVGProps } from "react";
import { PLATFORMS } from "@/lib/cinephile/data";
import type { Availability, ChatResponse, Movie, ReasoningStep } from "@/lib/cinephile/types";

type IconName = keyof typeof ICON_PATHS;

const ICON_PATHS = {
  film: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2.5" />
      <path d="M7 3v18M17 3v18M3 8h4M3 16h4M17 8h4M17 16h4M7 12h10" />
    </>
  ),
  clapper: (
    <>
      <path d="M3.5 8.5h17v11a1.5 1.5 0 0 1-1.5 1.5H5a1.5 1.5 0 0 1-1.5-1.5z" />
      <path d="M3.5 8.5 5 3.5l3.4.9-1.5 4.1M9.4 4.4l3.4.9-1.5 4.1M14.8 5.3l3.4.9-1.5 4.1" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 13a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V19a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 6.8 17l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H2a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 3.7 6.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H8a1.6 1.6 0 0 0 1-1.5V2a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V8a1.6 1.6 0 0 0 1.5 1H22a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z" />
    </>
  ),
  star: (
    <path
      d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.8 6.1 20.5l1.2-6.5L2.5 9.4l6.6-.9z"
      fill="currentColor"
      stroke="none"
    />
  ),
  send: <path d="M4 11.5 20 4l-7 16-2.5-7z" fill="currentColor" stroke="none" />,
  x: <path d="M6 6l12 12M18 6L6 18" />,
  chevdown: <path d="M5 8.5l7 7 7-7" />,
  chevright: <path d="M9 5l7 7-7 7" />,
  chevleft: <path d="M15 5l-7 7 7 7" />,
  layers: (
    <>
      <path d="M12 3 3 8l9 5 9-5z" />
      <path d="M3 13l9 5 9-5M3 18l9 5 9-5" />
    </>
  ),
  trending: (
    <>
      <path d="M3 17l6-6 4 4 7-8" />
      <path d="M14 7h6v6" />
    </>
  ),
  heart: (
    <path d="M12 20s-7-4.5-9.5-9C1 8 2.5 4.5 6 4.5c2 0 3.2 1.3 4 2.5.8-1.2 2-2.5 4-2.5 3.5 0 5 3.5 3.5 6.5C19 15.5 12 20 12 20z" />
  ),
  compare: (
    <>
      <rect x="3" y="4" width="7" height="16" rx="1.5" />
      <rect x="14" y="4" width="7" height="16" rx="1.5" />
    </>
  ),
  check: <path d="M5 12.5l4.5 4.5L19 7" />,
  bulb: (
    <>
      <path d="M9 18h6M10 21h4" />
      <path d="M12 3a6 6 0 0 0-4 10.5c.7.6 1 1 1 2v.5h6V15c0-1 .3-1.4 1-2A6 6 0 0 0 12 3z" />
    </>
  ),
  alert: (
    <>
      <path d="M12 8v5M12 16.5v.5" />
      <path d="M10.3 3.9 2.5 18a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
    </>
  ),
  retry: (
    <>
      <path d="M3 12a9 9 0 1 1 2.6 6.3" />
      <path d="M3 20v-5h5" />
    </>
  ),
  sparkle: (
    <path
      d="M12 2l1.6 6.4L20 10l-6.4 1.6L12 18l-1.6-6.4L4 10l6.4-1.6z"
      fill="currentColor"
      stroke="none"
    />
  ),
  play: <path d="M7 4.5l13 7.5-13 7.5z" fill="currentColor" stroke="none" />,
  newchat: (
    <>
      <path d="M21 11.5a8.5 8.5 0 0 1-12.3 7.6L3 21l1.9-5.7A8.5 8.5 0 1 1 21 11.5z" />
      <path d="M12 8v7M8.5 11.5h7" />
    </>
  ),
  tear: <path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z" />,
  smile: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 14.5a4.5 4.5 0 0 0 7 0M9 9.5h.01M15 9.5h.01" />
    </>
  ),
  pulse: <path d="M2 12h4l2.5-7 5 16 2.5-9H22" />,
  monitor: (
    <>
      <rect x="3" y="4" width="18" height="13" rx="2" />
      <path d="M8 21h8M12 17v4" />
    </>
  ),
  leaf: (
    <>
      <path d="M11 20A7 7 0 0 1 4 13c0-4 3-8 9-9 1 6-2 12-9 13z" />
      <path d="M4 20c4-4 6-6 7-9" />
    </>
  ),
  duo: (
    <>
      <circle cx="8" cy="9" r="3.2" />
      <circle cx="16" cy="9" r="3.2" />
      <path d="M3 19c0-2.8 2.2-5 5-5M21 19c0-2.8-2.2-5-5-5" />
    </>
  ),
  location: (
    <>
      <path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </>
  ),
} as const;

export function Icon({
  name,
  ...p
}: { name: IconName | string } & SVGProps<SVGSVGElement>) {
  const paths = ICON_PATHS[name as IconName];
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...p}
    >
      {paths}
    </svg>
  );
}

export function Poster({ m, showNet = true }: { m: Movie; showNet?: boolean }) {
  const bg = {
    background: `linear-gradient(155deg,
      hsl(${m.h1} 42% 24%) 0%,
      hsl(${m.h1} 38% 14%) 45%,
      hsl(${m.h2} 45% 10%) 100%)`,
  };
  const initials = m.title
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("");
  return (
    <div className="poster" style={bg}>
      {m.poster_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={m.poster_url}
          alt={m.title}
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
        />
      ) : (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "grid",
            placeItems: "center",
            overflow: "hidden",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 88,
              lineHeight: 1,
              color: `hsl(${m.h2} 60% 60% / .14)`,
              transform: "translateY(-6px)",
              letterSpacing: ".02em",
            }}
          >
            {initials}
          </span>
        </div>
      )}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(120% 80% at 50% -10%, rgba(255,255,255,.1), transparent 50%), linear-gradient(180deg, transparent 40%, rgba(0,0,0,.78))",
        }}
      />
      <div style={{ position: "absolute", left: 9, right: 9, bottom: 9 }}>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 14.5,
            lineHeight: 1.04,
            letterSpacing: ".01em",
            color: "#fff",
            textShadow: "0 2px 8px rgba(0,0,0,.6)",
            textTransform: "uppercase",
          }}
        >
          {m.title}
        </div>
        <div
          style={{
            fontSize: 10,
            color: "rgba(255,255,255,.6)",
            marginTop: 3,
            letterSpacing: ".04em",
          }}
        >
          {m.year}
        </div>
      </div>
      <span className="rate-chip">
        <Icon name="star" /> {m.rating.toFixed(1)}
      </span>
      {showNet && m.netflix && <span className="net-chip">NETFLIX</span>}
    </div>
  );
}

function MovieCard({ m }: { m: Movie }) {
  return (
    <div className="mcard" role="button" tabIndex={0}>
      <Poster m={m} />
      <div className="m-title">{m.title}</div>
      <div className="m-meta">
        {m.year} · {m.genres[0]}
      </div>
    </div>
  );
}

export function Carousel({
  movies,
  title = "Gợi ý cho bạn",
}: {
  movies: Movie[];
  title?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const scroll = (dir: number) =>
    ref.current?.scrollBy({ left: dir * 280, behavior: "smooth" });
  return (
    <div className="movies-block">
      <div className="movies-head">
        <Icon name="film" style={{ width: 14, height: 14 }} /> {title} · {movies.length}{" "}
        phim <span className="ln" />
      </div>
      <div className="carousel-wrap">
        <button
          type="button"
          className="car-arrow left"
          onClick={() => scroll(-1)}
          aria-label="Trước"
        >
          <Icon name="chevleft" />
        </button>
        <div className="carousel no-scrollbar" ref={ref}>
          {movies.map((m, i) => (
            <MovieCard key={i} m={m} />
          ))}
        </div>
        <button
          type="button"
          className="car-arrow right"
          onClick={() => scroll(1)}
          aria-label="Sau"
        >
          <Icon name="chevright" />
        </button>
      </div>
    </div>
  );
}

function PlatChip({ id, kind }: { id: string; kind?: string }) {
  const p = PLATFORMS[id as keyof typeof PLATFORMS];
  if (!p) return null;
  return (
    <div className="plat-chip">
      <span className="plat-logo" style={{ background: p.color, color: p.fg }}>
        {p.abbr || p.name[0]}
      </span>
      <span className="plat-meta">
        <span className="plat-name">{p.name}</span>
        {kind && <span className="plat-kind">{kind}</span>}
      </span>
    </div>
  );
}

function WhereToWatch({ where }: { where: NonNullable<Availability["where"]> }) {
  const { flatrate = [], rent = [], buy = [], soon = [] } = where;
  const rentBuy = [...new Set([...rent, ...buy])];
  return (
    <div className="wtw">
      <div className="wtw-head">
        <Icon name="location" style={{ width: 14, height: 14 }} /> Nơi xem tại Việt Nam
      </div>
      <div className={"wtw-net " + (where.netflix ? "ok" : "no")}>
        <span className="plat-logo" style={{ background: "#E50914", color: "#fff" }}>
          N
        </span>
        <span className="plat-name" style={{ flex: 1 }}>
          Netflix VN
        </span>
        <span className="wtw-flag">{where.netflix ? "Có sẵn" : "Không có"}</span>
      </div>
      {flatrate.filter((id) => id !== "netflix").length > 0 && (
        <div className="wtw-group">
          <div className="wtw-label green">Có trong gói thuê bao</div>
          <div className="wtw-row">
            {flatrate
              .filter((id) => id !== "netflix")
              .map((id) => (
                <PlatChip key={id} id={id} />
              ))}
          </div>
        </div>
      )}
      {rentBuy.length > 0 && (
        <div className="wtw-group">
          <div className="wtw-label">Thuê / Mua</div>
          <div className="wtw-row">
            {rentBuy.map((id) => (
              <PlatChip
                key={id}
                id={id}
                kind={
                  rent.includes(id) && buy.includes(id)
                    ? "Thuê · Mua"
                    : rent.includes(id)
                      ? "Thuê"
                      : "Mua"
                }
              />
            ))}
          </div>
        </div>
      )}
      {soon.length > 0 && (
        <div className="wtw-group">
          <div className="wtw-label faint">Có thể sắp có</div>
          <div className="wtw-row">
            {soon.map((id) => (
              <PlatChip key={id} id={id} kind="Dự kiến" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function BigCard({
  m,
  availability,
}: {
  m: Movie;
  availability?: Availability;
}) {
  return (
    <div className="movies-block">
      <div className="bigcard">
        <Poster m={m} showNet={false} />
        <div className="bc-body">
          <div className="bc-title">{m.title}</div>
          <div className="bc-sub">
            {m.year} · {m.genres.join(" · ")}
          </div>
          <div className="bc-stats">
            <span className="stat gold">
              <Icon name="star" /> {m.rating.toFixed(1)}
            </span>
            {availability ? (
              availability.netflix ? (
                <span className="stat green">
                  <Icon name="check" style={{ width: 12, height: 12 }} /> Có trên Netflix VN
                </span>
              ) : (
                <span className="stat">
                  <Icon name="alert" style={{ width: 12, height: 12 }} /> Không có trên Netflix VN
                </span>
              )
            ) : (
              <span className="stat">
                <Icon name="play" style={{ width: 11, height: 11 }} /> Xem trailer
              </span>
            )}
          </div>
          <div className="bc-overview">{m.overview}</div>
          {availability?.note && (
            <div
              className="bc-overview"
              style={{ color: "var(--text-mut)" }}
              dangerouslySetInnerHTML={{ __html: availability.note }}
            />
          )}
        </div>
      </div>
      {availability?.where && <WhereToWatch where={availability.where} />}
    </div>
  );
}

export function Compare({
  movies,
  note,
}: {
  movies: Movie[];
  note?: string;
}) {
  return (
    <div className="movies-block">
      <div className="movies-head">
        <Icon name="compare" style={{ width: 14, height: 14 }} /> So sánh <span className="ln" />
      </div>
      <div className="compare-grid">
        {movies.map((m, i) => (
          <div
            className="bigcard"
            key={i}
            style={{ flexDirection: "column", alignItems: "center", textAlign: "center" }}
          >
            <div style={{ width: 108 }}>
              <Poster m={m} showNet={false} />
            </div>
            <div className="bc-body" style={{ alignItems: "center" }}>
              <div className="bc-title" style={{ fontSize: 20 }}>
                {m.title}
              </div>
              <div className="bc-stats" style={{ justifyContent: "center" }}>
                <span className="stat gold">
                  <Icon name="star" /> {m.rating.toFixed(1)}
                </span>
                {m.netflix && <span className="stat green">Netflix VN</span>}
              </div>
              <div className="bc-genres" style={{ justifyContent: "center" }}>
                {m.genres.map((g, j) => (
                  <span className="genre-tag" key={j}>
                    {g}
                  </span>
                ))}
              </div>
              <div className="bc-overview">{m.overview}</div>
            </div>
          </div>
        ))}
      </div>
      {note && (
        <div
          className="bubble ai"
          style={{ borderTopLeftRadius: 12 }}
          dangerouslySetInnerHTML={{ __html: note }}
        />
      )}
    </div>
  );
}

export function DuoResult({
  tasteA,
  tasteB,
  picks,
}: {
  tasteA: string;
  tasteB: string;
  picks: NonNullable<ChatResponse["duoPicks"]>;
}) {
  return (
    <div className="movies-block">
      <div className="duo-tastes">
        <span className="duo-tag a">{tasteA}</span>
        <span className="duo-x">
          <Icon name="duo" style={{ width: 16, height: 16 }} />
        </span>
        <span className="duo-tag b">{tasteB}</span>
      </div>
      <div className="duo-list">
        {picks.map((p, i) => (
          <div className="duo-item" key={i}>
            <div style={{ width: 64, flexShrink: 0 }}>
              <Poster m={p.m} showNet={false} />
            </div>
            <div className="duo-body">
              <div className="duo-title">
                {p.m.title} <span className="duo-year">{p.m.year}</span>
              </div>
              <div className="duo-stats">
                <span className="stat gold" style={{ padding: "3px 7px", fontSize: 11 }}>
                  <Icon name="star" /> {p.m.rating.toFixed(1)}
                </span>
                <span style={{ fontSize: 11.5, color: "var(--text-faint)" }}>
                  {p.m.genres.join(" · ")}
                </span>
              </div>
              <div className="duo-why" dangerouslySetInnerHTML={{ __html: p.why }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ReasoningPanel({ steps }: { steps: ReasoningStep[] }) {
  const [open, setOpen] = useState(false);
  if (!steps?.length) return null;
  return (
    <div className={"reason" + (open ? " open" : "")}>
      <button type="button" className="reason-head" onClick={() => setOpen((o) => !o)}>
        <Icon name="bulb" style={{ width: 15, height: 15, color: "var(--orange)" }} />
        Quy trình suy luận
        <span className="badge">{steps.length} bước</span>
        <span className="chev">
          <Icon name="chevdown" />
        </span>
      </button>
      <div className="reason-body">
        <div>
          <div className="reason-steps">
            {steps.map((s, i) => (
              <Fragment key={i}>
                <div className="rstep thought">
                  <div className="rail">
                    <span className="node" />
                    <span className="line" />
                  </div>
                  <div className="rcontent">
                    <div className="rlabel">Suy nghĩ</div>
                    <div className="rtext">{s.thought}</div>
                  </div>
                </div>
                <div className="rstep action">
                  <div className="rail">
                    <span className="node" />
                    <span className="line" />
                  </div>
                  <div className="rcontent">
                    <div className="rlabel">Hành động</div>
                    <div className="rtext">
                      <code>{s.action}</code>
                    </div>
                  </div>
                </div>
                <div className="rstep observe">
                  <div className="rail">
                    <span className="node" />
                    <span className="line" />
                  </div>
                  <div className="rcontent">
                    <div className="rlabel">Quan sát</div>
                    <div className="rtext">{s.observe}</div>
                  </div>
                </div>
              </Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
