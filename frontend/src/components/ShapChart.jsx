export default function ShapChart({ contributions }) {
  const max = Math.max(...contributions.map((c) => c.value));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h4 className="text-[14px] font-bold text-slate-900">Why was this flagged? (Z-Score Attribution)</h4>
      <p className="mt-1 text-[12px] text-slate-500 font-medium">
        Z-Score statistical contribution to the anomaly score, largest impact first.
      </p>

      <div className="mt-6 space-y-4">
        {contributions.map((c) => (
          <div key={c.feature}>
            <div className="mb-1.5 flex items-center justify-between text-[12px]">
              <span className="font-medium text-slate-800">{c.feature}</span>
              <span className="font-mono-num font-bold text-sky-700">
                +{c.value.toFixed(2)}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-sky-600 to-sky-400 transition-all duration-700"
                style={{ width: `${(c.value / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-6 border-t border-slate-100 pt-4 text-[12px] leading-relaxed text-slate-500 font-medium">
        Temperature and its rate of change were the primary contributors to the anomaly score.
      </p>
    </div>
  );
}
