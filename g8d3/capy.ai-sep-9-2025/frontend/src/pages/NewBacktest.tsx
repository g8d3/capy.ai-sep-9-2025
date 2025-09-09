import { useEffect, useState } from "react";
import AssetSearch from "../components/AssetSearch";
import StrategyFormRSI from "../components/StrategyFormRSI";
import { api } from "../api/client";

export default function NewBacktest() {
  const [assets, setAssets] = useState<string[]>([]);
  const [start, setStart] = useState<string>("-3y");
  const [end, setEnd] = useState<string>("now");
  const [fees, setFees] = useState<number>(10);
  const [slippage, setSlippage] = useState<number>(5);
  const [rsi, setRsi] = useState({ period: 14, lower: 30, upper: 70 });
  const [submitting, setSubmitting] = useState(false);
  const [job, setJob] = useState<{ id: number; job_id: string } | null>(null);

  const removeAsset = (s: string) => setAssets((prev) => prev.filter((x) => x !== s));

  const submit = async () => {
    setSubmitting(true);
    try {
      const payload = {
        assets,
        timeframe: "1h",
        start,
        end,
        strategy: { type: "rsi_threshold", params: rsi },
        fees_bps: fees,
        slippage_bps: slippage,
      };
      const res = await api.post("/api/v1/backtests", payload);
      setJob(res.data);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">New Backtest</h1>

      <div>
        <label className="block text-sm font-medium">Assets</label>
        <AssetSearch onAdd={(s) => setAssets((prev) => (prev.includes(s) ? prev : [...prev, s]))} />
        <div className="mt-2 flex flex-wrap gap-2">
          {assets.map((a) => (
            <span key={a} className="rounded bg-slate-100 px-2 py-1 text-sm">
              {a} <button className="ml-2 text-red-600" onClick={() => removeAsset(a)}>x</button>
            </span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm">Start</label>
          <input className="w-full rounded border p-2" value={start} onChange={(e) => setStart(e.target.value)} />
          <div className="text-xs text-muted-foreground">Use -3y, -180d, -72h or Unix ms</div>
        </div>
        <div>
          <label className="block text-sm">End</label>
          <input className="w-full rounded border p-2" value={end} onChange={(e) => setEnd(e.target.value)} />
          <div className="text-xs text-muted-foreground">Use 'now' or Unix ms</div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium">RSI Strategy</label>
        <StrategyFormRSI value={rsi} onChange={setRsi} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm">Fees (bps)</label>
          <input type="number" className="w-full rounded border p-2" value={fees} onChange={(e) => setFees(parseFloat(e.target.value || "0"))} />
        </div>
        <div>
          <label className="block text-sm">Slippage (bps)</label>
          <input type="number" className="w-full rounded border p-2" value={slippage} onChange={(e) => setSlippage(parseFloat(e.target.value || "0"))} />
        </div>
      </div>

      <button disabled={submitting || assets.length === 0} className="rounded bg-black px-4 py-2 text-white disabled:opacity-50" onClick={submit}>
        {submitting ? "Submitting..." : "Run Backtest"}
      </button>

      {job && (
        <div className="rounded border p-3 text-sm">Enqueued backtest #{job.id}. <a className="underline" href={`/backtests/${job.id}`}>View status</a></div>
      )}
    </div>
  );
}
