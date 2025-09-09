import { useEffect, useState } from "react";
import { api } from "../api/client";

type SearchItem = {
  cg_id: string;
  name: string;
  symbol: string;
  possible_exchange_symbols: string[];
};

export default function AssetSearch({ onAdd }: { onAdd: (symbol: string) => void }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchItem[]>([]);

  useEffect(() => {
    const t = setTimeout(async () => {
      if (q.length < 2) return setResults([]);
      const res = await api.get<SearchItem[]>("/api/v1/assets/search", { params: { q } });
      setResults(res.data);
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <div>
      <input className="w-full rounded border p-2" placeholder="Search assets (e.g., btc)" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="mt-2 space-y-2">
        {results.map((r) => (
          <div key={r.cg_id} className="flex items-center justify-between rounded border p-2">
            <div>
              <div className="font-medium">{r.name} ({r.symbol})</div>
              <div className="text-sm text-muted-foreground">{r.possible_exchange_symbols.join(", ")}</div>
            </div>
            <div className="flex gap-2">
              {r.possible_exchange_symbols.map((s) => (
                <button key={s} className="rounded bg-slate-100 px-2 py-1 text-sm" onClick={() => onAdd(s)}>
                  Add {s}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
