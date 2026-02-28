import type { SimulationState } from "../../types/simulation";

interface Props {
  simulation: SimulationState;
}

const EMOTION_COLOR: Record<string, string> = {
  engaged: "bg-green-500",
  passive: "bg-gray-400",
  anxious: "bg-orange-400",
  confused: "bg-purple-400",
  disruptive: "bg-red-400",
};

// Placeholder panel -- metrics and charts will be added once simulation schema is finalised.
export default function ResultsPanel({ simulation }: Props) {
  if (simulation.status === "idle") return null;

  const counts = simulation.students.reduce<Record<string, number >>((acc, s) => {
    acc[s.emotion] = (acc[s.emotion] ?? 0) + 1;
    return acc;
  }, {});

  const total = simulation.students.length || 30;
  const engagedCount = counts["engaged"] ?? 0;
  const pct = Math.round((engagedCount / total) * 100);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-bold text-gray-800"> Results </h2>

      <div className="rounded-xl border border-gray-200 bg-white p-4 flex flex-col gap-3">
        <p className="text-sm font-semibold text-gray-600"> Class Engagement </p>
        <div className="flex items-end gap-2">
          <span className="text-4xl font-bold text-green-600">{pct}%</span>
          <span className="text-sm text-gray-400 mb-1"> engaged </span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{ width: pct + "%" }}
          />
        </div>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <p className="text-sm font-semibold text-gray-600 mb-3"> Student States </p>
        <div className="flex flex-col gap-2">
          {Object.entries(counts).map(([emotion, count]) => (
            <div key={emotion} className="flex items-center gap-2">
              <span className={"w-3 h-3 rounded-full shrink-0 " + (EMOTION_COLOR[emotion] ?? "bg-gray-300")} />
              <span className="text-sm text-gray-700 capitalize w-20">{emotion}</span>
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={"h-full rounded-full " + (EMOTION_COLOR[emotion] ?? "bg-gray-300")}
                  style={{ width: Math.round((count / total) * 100) + "%" }}
                />
              </div>
              <span className="text-xs text-gray-400 w-6 text-right">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-gray-400 text-center">
        {simulation.status === "running" ? "Live — updating" : "Final results"}
      </p>
    </div>
  );
}
