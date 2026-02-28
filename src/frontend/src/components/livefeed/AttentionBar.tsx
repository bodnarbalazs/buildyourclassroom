import type { CollectiveAttention } from "../../lib/livefeed-types";

function scoreColor(score: number): string {
  if (score < 0.3) return "bg-red-500";
  if (score < 0.6) return "bg-yellow-500";
  return "bg-green-500";
}

export default function AttentionBar({
  attention,
}: {
  attention: CollectiveAttention;
}) {
  const pct = Math.round(attention.score * 100);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 px-6 py-3 flex items-center justify-between z-20">
      <div className="flex items-center gap-4">
        <div className="w-48 h-3 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${scoreColor(attention.score)}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-white text-sm font-medium">
          Attention: {pct}%
        </span>
      </div>
      <span className="text-gray-400 text-sm">
        {attention.activeCameras}/{attention.maxCameras} streams active &bull;{" "}
        {attention.totalFaces} faces detected
      </span>
    </div>
  );
}
