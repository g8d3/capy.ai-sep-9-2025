import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Backtests() {
  const [items, setItems] = useState<any[]>([]);

  const load = async () => {
    const res = await api.get("/api/v1/backtests", { params: { limit: 50, offset: 0 } });
    setItems(res.data.items);
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Backtests</h1>
        <a className="rounded bg-black px-3 py-2 text-white" href="/new">New Backtest</a>
      </div>
      <table className="w-full text-left">
        <thead>
          <tr className="border-b">
            <th className="py-2">ID</th>
            <th>Status</th>
            <th>Progress</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.id} className="border-b">
              <td className="py-2">{it.id}</td>
              <td className="capitalize">{it.status}</td>
              <td>{Math.round((it.progress || 0) * 100)}%</td>
              <td>{new Date(it.created_at).toLocaleString()}</td>
              <td><a className="underline" href={`/backtests/${it.id}`}>Open</a></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
