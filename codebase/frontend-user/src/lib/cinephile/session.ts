/**
 * Phiên chat chỉ sống trong tab hiện tại (không lưu localStorage).
 * F5 / refresh → state React reset → sessionId mới → backend coi là phiên mới.
 * Bấm "Trò chuyện mới" cũng tạo sessionId mới.
 */

export function newSessionId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}
