import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { Emotion, SimulationState, TickSnapshot } from "../../types/simulation";

interface Props {
  simulation: SimulationState;
  ticks: TickSnapshot[];
}

const EMOTIONS: Emotion[] = ["engaged", "passive", "anxious", "confused", "disruptive"];

const EMOTION_STYLE: Record<Emotion, { fill: string; stroke: string; tw: string }> = {
  engaged:    { fill: "#22c55e", stroke: "#16a34a", tw: "bg-green-500" },
  passive:    { fill: "#9ca3af", stroke: "#6b7280", tw: "bg-gray-400" },
  anxious:    { fill: "#fb923c", stroke: "#ea580c", tw: "bg-orange-400" },
  confused:   { fill: "#a78bfa", stroke: "#7c3aed", tw: "bg-purple-400" },
  disruptive: { fill: "#f87171", stroke: "#dc2626", tw: "bg-red-400" },
};

interface ChartRow {
  minute: number;
  engaged: number;
  passive: number;
  anxious: number;
  confused: number;
  disruptive: number;
}

function buildChartData(ticks: TickSnapshot[]): ChartRow[] {
  return ticks.map((tick) => {
    const counts: Record<string, number> = {};
    for (const s of tick.students) {
      counts[s.emotion] = (counts[s.emotion] ?? 0) + 1;
    }
    return {
      minute: tick.cycle,
      engaged: counts["engaged"] ?? 0,
      passive: counts["passive"] ?? 0,
      anxious: counts["anxious"] ?? 0,
      confused: counts["confused"] ?? 0,
      disruptive: counts["disruptive"] ?? 0,
    };
  });
}

export default function ResultsPanel({ simulation, ticks }: Props) {
  const chartData = useMemo(() => buildChartData(ticks), [ticks]);

  if (simulation.status === "idle") return null;

  const counts = simulation.students.reduce<Record<string, number>>((acc, s) => {
    acc[s.emotion] = (acc[s.emotion] ?? 0) + 1;
    return acc;
  }, {});

  const total = simulation.students.length || 30;
  const engagedCount = counts["engaged"] ?? 0;
  const pct = Math.round((engagedCount / total) * 100);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-bold text-gray-800">Results</h2>

      {/* Engagement summary */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 flex flex-col gap-3">
        <p className="text-sm font-semibold text-gray-600">Class Engagement</p>
        <div className="flex items-end gap-2">
          <span className="text-4xl font-bold text-green-600">{pct}%</span>
          <span className="text-sm text-gray-400 mb-1">engaged</span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{ width: pct + "%" }}
          />
        </div>
      </div>

      {/* Student states bar */}
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <p className="text-sm font-semibold text-gray-600 mb-3">Student States</p>
        <div className="flex flex-col gap-2">
          {Object.entries(counts).map(([emotion, count]) => (
            <div key={emotion} className="flex items-center gap-2">
              <span className={"w-3 h-3 rounded-full shrink-0 " + (EMOTION_STYLE[emotion as Emotion]?.tw ?? "bg-gray-300")} />
              <span className="text-sm text-gray-700 capitalize w-20">{emotion}</span>
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: Math.round((count / total) * 100) + "%",
                    backgroundColor: EMOTION_STYLE[emotion as Emotion]?.fill ?? "#d1d5db",
                  }}
                />
              </div>
              <span className="text-xs text-gray-400 w-6 text-right">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Timeline chart */}
      {chartData.length > 1 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <p className="text-sm font-semibold text-gray-600 mb-3">Emotion Timeline</p>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="minute"
                tick={{ fontSize: 11 }}
                label={{ value: "Minute", position: "insideBottomRight", offset: -5, fontSize: 11, fill: "#9ca3af" }}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                label={{ value: "Students", angle: -90, position: "insideLeft", offset: 10, fontSize: 11, fill: "#9ca3af" }}
              />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
                labelFormatter={(v) => `Minute ${v}`}
              />
              <Legend
                wrapperStyle={{ fontSize: 11 }}
                formatter={(value: string) => value.charAt(0).toUpperCase() + value.slice(1)}
              />
              {EMOTIONS.map((emotion) => (
                <Area
                  key={emotion}
                  type="monotone"
                  dataKey={emotion}
                  stackId="1"
                  fill={EMOTION_STYLE[emotion].fill}
                  stroke={EMOTION_STYLE[emotion].stroke}
                  fillOpacity={0.7}
                />
              ))}
              {simulation.status === "running" && (
                <ReferenceLine x={simulation.currentMinute} stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 4" />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="text-xs text-gray-400 text-center">
        {simulation.status === "running" ? "Live — updating" : "Final results"}
      </p>
    </div>
  );
}
