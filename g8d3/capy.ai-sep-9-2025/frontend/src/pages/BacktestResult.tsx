import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api, API_BASE_URL } from "../api/client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

function parseCsv(text: string) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const parts = line.split(",");
    const obj: any = {};
    headers.forEach((h, i) => (obj[h] = parts[i]));
    return obj;
  });
}

function fmt(v: any) {
  if (v === null || v === undefined || Number.isNaN(v)) return '-';
  if (typeof v === 'number') return v.toFixed(4);
  return String(v);
}

export default function BacktestResult() {
  const { id } = useParams();
  const [bt, setBt] = useState<any | null>(null);
  const [equity, setEquity] = useState<any[]>([]);

  const load = async () => {
    const res = await api.get(`/api/v1/backtests/${id}`);
    setBt(res.data);
    if (res.data.status === "completed") {
      const csv = await api.get(`/api/v1/backtests/${id}/download`, { params: { kind: "equity" }, responseType: "text" });
      const rows = parseCsv(csv.data);
      const points = rows.map((r: any) => ({ t: new Date(parseInt(r["timestamp"])) as any, equity: parseFloat(r["equity"]) }));
      setEquity(points);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [id]);

  const drawdown = useMemo(() => {
    let peak = 0;
    return equity.map((p) => {
      peak = Math.max(peak, p.equity);
      const dd = peak > 0 ? (p.equity / peak - 1) : 0;
      return { t: p.t, dd };
    });
  }, [equity]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Backtest #{id}</h1>
      {bt && (
        <div className="rounded border p-3 text-sm">
          <div>Status: <span className="capitalize">{bt.status}</span> ({Math.round((bt.progress || 0) * 100)}%)</div>
          {bt.metrics?.aggregate && (
            <div className="mt-2 grid grid-cols-2 gap-2 md:grid-cols-4">
              {Object.entries(bt.metrics.aggregate).map(([k, v]) => (
                <div key={k}><span className="text-muted-foreground">{k}</span>: {typeof v === 'number' ? v.toFixed(4) : String(v)}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {bt?.assets?.length > 0 && (
        <div className="rounded border p-3">
          <div className="mb-2 font-medium">Per-asset Metrics</div>
          <table className="w-full text-left">
            <thead>
              <tr className="border-b">
                <th className="py-2">Asset</th>
                <th>CAGR</th>
                <th>Sharpe</th>
                <th>MaxDD</th>
                <th>Trades</th>
                <th>WinRate</th>
              </tr>
            </thead>
            <tbody>
              {bt.assets.map((a: any) => (
                <tr key={a.asset_id} className="border-b">
                  <td className="py-2">{a.exchange_symbol}</td>
                  <td>{fmt(a.metrics?.CAGR)}</td>
                  <td>{fmt(a.metrics?.Sharpe)}</td>
                  <td>{fmt(a.metrics?.MaxDD)}</td>
                  <td>{a.metrics?.Trades ?? '-'}</td>
                  <td>{fmt(a.metrics?.WinRate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {equity.length > 0 && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="h-64 rounded border p-3">
            <div className="mb-2 font-medium">Equity Curve</div>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="t" tickFormatter={(v) => new Date(v).toLocaleDateString()} />
                <YAxis />
                <Tooltip labelFormatter={(v) => new Date(v).toLocaleString()} formatter={(v: number) => v.toFixed(4)} />
                <Line type="monotone" dataKey="equity" stroke="#2563eb" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="h-64 rounded border p-3">
            <div className="mb-2 font-medium">Drawdown</div>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={drawdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="t" tickFormatter={(v) => new Date(v).toLocaleDateString()} />
                <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <Tooltip labelFormatter={(v) => new Date(v).toLocaleString()} formatter={(v: number) => `${(v * 100).toFixed(2)}%`} />
                <Area type="monotone" dataKey="dd" stroke="#ef4444" fill="#fecaca" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {bt?.status === "completed" && (
        <div>
          <a className="rounded bg-slate-800 px-3 py-2 text-white" href={`${API_BASE_URL}/api/v1/backtests/${id}/download?kind=equity`} target="_blank">Download Equity CSV</a>
          <a className="ml-2 rounded bg-slate-800 px-3 py-2 text-white" href={`${API_BASE_URL}/api/v1/backtests/${id}/download?kind=trades`} target="_blank">Download Trades CSV</a>
        </div>
      )}
    </div>
  );
}
