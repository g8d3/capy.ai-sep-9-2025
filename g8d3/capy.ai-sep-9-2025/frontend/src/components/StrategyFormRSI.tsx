import { useState, useEffect } from "react";

type Props = {
  value: { period: number; lower: number; upper: number };
  onChange: (v: { period: number; lower: number; upper: number }) => void;
};

export default function StrategyFormRSI({ value, onChange }: Props) {
  const [period, setPeriod] = useState(value.period);
  const [lower, setLower] = useState(value.lower);
  const [upper, setUpper] = useState(value.upper);

  useEffect(() => {
    onChange({ period, lower, upper });
  }, [period, lower, upper]);

  return (
    <div className="grid grid-cols-3 gap-4">
      <div>
        <label className="block text-sm">RSI Period</label>
        <input type="number" className="w-full rounded border p-2" value={period} onChange={(e) => setPeriod(parseInt(e.target.value || "0"))} />
      </div>
      <div>
        <label className="block text-sm">Lower</label>
        <input type="number" className="w-full rounded border p-2" value={lower} onChange={(e) => setLower(parseFloat(e.target.value || "0"))} />
      </div>
      <div>
        <label className="block text-sm">Upper</label>
        <input type="number" className="w-full rounded border p-2" value={upper} onChange={(e) => setUpper(parseFloat(e.target.value || "0"))} />
      </div>
    </div>
  );
}
