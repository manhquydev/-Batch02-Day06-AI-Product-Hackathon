"use client";

export type HistoryEntry = {
  id: number;
  query: string;
  latency: number;
  model: string;
  timestamp: string;
};

type Props = {
  entries: HistoryEntry[];
  open: boolean;
  onToggle: () => void;
  onSelect: (entry: HistoryEntry) => void;
};

export function HistorySidebar({ entries, open, onToggle, onSelect }: Props) {
  return (
    <>
      {/* Toggle tab on right edge */}
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-zinc-800 border border-zinc-700 border-r-0 rounded-l-lg px-2 py-4 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition-colors select-none"
        style={{ writingMode: "vertical-rl" }}
        title={open ? "Close history" : `History (${entries.length})`}
      >
        {open ? "✕ Close" : `History${entries.length > 0 ? ` (${entries.length})` : ""}`}
      </button>

      {/* Panel */}
      {open && (
        <div className="fixed right-0 top-0 h-full w-72 bg-zinc-900 border-l border-zinc-700 flex flex-col z-50 shadow-2xl">
          <div className="px-4 py-3 border-b border-zinc-700 flex items-center justify-between shrink-0">
            <h2 className="text-sm font-semibold text-zinc-200">Query History</h2>
            <button
              onClick={onToggle}
              className="text-zinc-500 hover:text-zinc-300 text-lg leading-none"
            >
              ✕
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {entries.length === 0 ? (
              <p className="text-xs text-zinc-500 p-4">No queries yet.</p>
            ) : (
              entries.map((e) => (
                <button
                  key={e.id}
                  onClick={() => onSelect(e)}
                  className="w-full text-left px-4 py-3 border-b border-zinc-800 hover:bg-zinc-800 transition-colors group"
                >
                  <p className="text-sm text-zinc-300 truncate group-hover:text-white">{e.query}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-zinc-500 font-mono">{e.timestamp}</span>
                    <span className="text-xs text-blue-400 font-mono">{e.latency}ms</span>
                    <span className="text-xs text-zinc-600 font-mono truncate">{e.model}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </>
  );
}
