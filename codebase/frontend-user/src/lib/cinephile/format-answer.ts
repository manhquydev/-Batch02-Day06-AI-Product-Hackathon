/** Chuyển markdown từ agent backend → HTML an toàn cho bubble chat. */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inlineMarkdown(text: string): string {
  let s = escapeHtml(text);
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  return s;
}

/** Bỏ khối chi tiết phim (đã có carousel); giữ đoạn mở đầu. */
export function extractIntroParagraph(answer: string): string {
  const lines = answer.replace(/\r\n/g, "\n").split("\n");
  const intro: string[] = [];

  for (const line of lines) {
    const t = line.trim();
    if (!t) {
      if (intro.length) break;
      continue;
    }
    if (/^!\[/.test(t)) continue;
    if (/^\d+\.\s/.test(t)) break;
    if (/^\*\*[^*]+\*\*\s*$/.test(t) && intro.length > 0) break;
    if (/^[-*]\s/.test(t) && /thể loại|đánh giá|genre|rating/i.test(t)) break;
    intro.push(t);
  }

  const joined = intro.join(" ").trim();
  if (joined) return joined;

  const first = lines.map((l) => l.trim()).find((l) => l && !/^!\[/.test(l));
  return first || "Đây là gợi ý phim cho bạn:";
}

export function markdownToHtml(markdown: string): string {
  const trimmed = markdown.trim();
  if (!trimmed) return "<p></p>";

  const lines = trimmed.replace(/\r\n/g, "\n").split("\n");
  const parts: string[] = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      parts.push("</ul>");
      inList = false;
    }
  };

  for (const line of lines) {
    const raw = line.trim();
    if (!raw) {
      closeList();
      continue;
    }

    if (/^!\[[^\]]*\]\([^)]+\)\s*$/.test(raw)) continue;

    const bullet = raw.match(/^[-*]\s+(.+)$/);
    const numbered = raw.match(/^\d+\.\s+(.+)$/);

    if (bullet || numbered) {
      if (!inList) {
        parts.push("<ul>");
        inList = true;
      }
      parts.push("<li>" + inlineMarkdown((bullet || numbered)![1]) + "</li>");
      continue;
    }

    closeList();
    parts.push("<p>" + inlineMarkdown(raw) + "</p>");
  }

  closeList();
  return parts.length ? parts.join("") : "<p></p>";
}

/** HTML hiển thị trong bubble — rút gọn khi đã có carousel phim. */
export function formatAnswerHtml(
  answer: string,
  options?: { compact?: boolean },
): string {
  const source = options?.compact ? extractIntroParagraph(answer) : answer;
  return markdownToHtml(source);
}
