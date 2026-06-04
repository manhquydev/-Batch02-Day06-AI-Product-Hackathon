"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import { deleteAdminSession, fetchAdminSession, fetchAdminSessions } from "@/lib/api";
import type { AdminSessionDetail, AdminSessionSummary } from "@/lib/types";

export function UsersTab() {
  const [sessions, setSessions] = useState<AdminSessionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AdminSessionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAdminSessions();
      setSessions(data.sessions);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  async function handleSelect(id: string) {
    if (selected?.id === id) {
      setSelected(null);
      return;
    }
    setDetailLoading(true);
    try {
      const detail = await fetchAdminSession(id);
      setSelected(detail);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteAdminSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (selected?.id === id) setSelected(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="max-w-5xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-200">User Sessions</h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            {sessions.length} active session{sessions.length !== 1 ? "s" : ""} in memory
          </p>
        </div>
        <button
          onClick={loadSessions}
          disabled={loading}
          className="px-3 py-1.5 text-xs bg-zinc-800 border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-white rounded transition-colors disabled:opacity-50"
        >
          {loading ? "Refreshing…" : "↻ Refresh"}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-900/40 border border-red-700 rounded text-red-300 text-xs">
          {error}
        </div>
      )}

      {!loading && sessions.length === 0 && !error && (
        <p className="text-sm text-zinc-500 py-8 text-center">
          No sessions yet. Users will appear here after they start chatting.
        </p>
      )}

      {sessions.length > 0 && (
        <div className="border border-zinc-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-700 bg-zinc-800/50">
                <th className="px-4 py-2.5 text-left text-xs font-medium text-zinc-400">Session ID</th>
                <th className="px-4 py-2.5 text-center text-xs font-medium text-zinc-400">Turns</th>
                <th className="px-4 py-2.5 text-center text-xs font-medium text-zinc-400">Summary</th>
                <th className="px-4 py-2.5 text-center text-xs font-medium text-zinc-400">Rejected</th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-zinc-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s, i) => (
                <Fragment key={s.id}>
                  <tr
                    className={`border-b border-zinc-800 hover:bg-zinc-800/40 cursor-pointer transition-colors ${
                      selected?.id === s.id ? "bg-zinc-800/60" : i % 2 === 0 ? "" : "bg-zinc-900/30"
                    }`}
                    onClick={() => handleSelect(s.id)}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-zinc-300">
                      <span title={s.id}>{s.id.slice(0, 8)}…</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-zinc-200 font-medium">{s.turn_count}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {s.has_summary ? (
                        <span className="px-2 py-0.5 text-xs bg-emerald-900/40 text-emerald-400 border border-emerald-800 rounded">
                          yes
                        </span>
                      ) : (
                        <span className="text-zinc-600 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center text-zinc-400 text-xs">
                      {s.rejected_count > 0 ? (
                        <span className="text-amber-400">{s.rejected_count}</span>
                      ) : (
                        "0"
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(s.id);
                        }}
                        className="text-xs text-zinc-600 hover:text-red-400 transition-colors px-2 py-1 rounded hover:bg-red-900/20"
                        title="Delete session"
                      >
                        ✕
                      </button>
                    </td>
                  </tr>

                  {selected?.id === s.id && (
                    <tr className="border-b border-zinc-700">
                      <td colSpan={5} className="p-0">
                        <SessionDetail
                          detail={selected}
                          loading={detailLoading}
                        />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SessionDetail({
  detail,
  loading,
}: {
  detail: AdminSessionDetail;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="px-6 py-4 text-xs text-zinc-500 flex items-center gap-2">
        <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        Loading…
      </div>
    );
  }

  return (
    <div className="bg-zinc-950/60 px-6 py-4 space-y-4">
      <div className="flex items-center gap-4 text-xs text-zinc-500">
        <span>
          Full ID: <span className="font-mono text-zinc-400">{detail.id}</span>
        </span>
        {detail.rejected_movie_ids.length > 0 && (
          <span>
            Rejected IDs:{" "}
            <span className="text-amber-400 font-mono">
              {detail.rejected_movie_ids.join(", ")}
            </span>
          </span>
        )}
      </div>

      {detail.summary && (
        <div className="p-3 bg-emerald-900/20 border border-emerald-800/50 rounded text-xs text-emerald-300">
          <span className="text-emerald-600 font-medium mr-2">Summary:</span>
          {detail.summary}
        </div>
      )}

      {detail.turns.length === 0 ? (
        <p className="text-xs text-zinc-600">No turns recorded.</p>
      ) : (
        <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
          {detail.turns.map((turn, idx) => (
            <div key={idx} className="space-y-1.5">
              <div className="flex gap-2">
                <span className="text-xs font-medium text-blue-400 shrink-0 w-16">User</span>
                <p className="text-xs text-zinc-300 leading-relaxed">{turn.user}</p>
              </div>
              <div className="flex gap-2">
                <span className="text-xs font-medium text-emerald-400 shrink-0 w-16">Agent</span>
                <p className="text-xs text-zinc-400 leading-relaxed whitespace-pre-wrap">
                  {turn.assistant}
                </p>
              </div>
              {idx < detail.turns.length - 1 && (
                <hr className="border-zinc-800 mt-2" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
