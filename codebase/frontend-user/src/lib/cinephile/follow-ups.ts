import type { ChatResponse, FollowUpChip, Movie } from "./types";

const EXPLORE: FollowUpChip[] = [
  { text: "Phim Sci-Fi trending tuần này ở VN", kind: "explore" },
  { text: "Gợi ý phim hài nhẹ để xem tối nay", kind: "explore" },
  { text: "Phim lãng mạn hợp xem hẹn hò", kind: "explore" },
  { text: "So sánh Inception và Interstellar", kind: "explore" },
];

function primaryGenre(movies: Movie[]): string {
  const g = movies[0]?.genres?.[0];
  return g || "phim";
}

/** Gợi ý tiếp theo cho chế độ mock (không gọi API). */
export function mockFollowUps(userText: string, res: ChatResponse): FollowUpChip[] {
  if (res.kind === "refuse") {
    return res.refuseChips?.map((text) => ({ text, kind: "explore" as const })) ?? EXPLORE;
  }
  if (res.kind === "error") return [];

  const movies = res.movies ?? [];
  const chips: FollowUpChip[] = [];

  if (movies.length > 0) {
    for (const m of movies.slice(0, 3)) {
      chips.push({
        text: `Cho mình biết thêm về phim ${m.title}`,
        kind: "detail",
      });
    }
    chips.push({
      text: `Phim ${movies[0].title} có trên Netflix VN không?`,
      kind: "continue",
    });
    if (movies.length >= 2) {
      chips.push({
        text: `So sánh ${movies[0].title} và ${movies[1].title}`,
        kind: "continue",
      });
    } else {
      chips.push({
        text: `Gợi ý phim tương tự ${movies[0].title}`,
        kind: "continue",
      });
    }
    if (/\b\d+\s*phim\b/i.test(userText) && movies.length >= 2) {
      const genre = primaryGenre(movies);
      chips.push({
        text: `Cho tôi 3 phim ${genre} khác nữa`,
        kind: "continue",
      });
    }
  }

  const lower = userText.toLowerCase();
  for (const e of EXPLORE) {
    if (!lower.includes(e.text.slice(0, 12).toLowerCase())) {
      chips.push(e);
    }
    if (chips.length >= 4) break;
  }

  while (chips.length < 3) {
    chips.push(EXPLORE[chips.length % EXPLORE.length]);
  }

  const seen = new Set<string>();
  return chips
    .filter((c) => {
      const k = c.text.toLowerCase();
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    })
    .slice(0, 4);
}
