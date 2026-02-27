import { useState } from "react";
import type { LessonPlan, LessonSegment } from "../../types/simulation";

interface Props {
  onPlanReady: (plan: LessonPlan) => void;
  onRunSimulation: () => void;
  simulationStatus: "idle" | "running" | "done";
}

// Placeholder structure -- will be replaced with LLM API call
function mockStructure(_text: string): LessonSegment[] {
  return [
    { startMinute: 0, endMinute: 5, title: "Introduction", description: "Warm-up and review" },
    { startMinute: 5, endMinute: 20, title: "New Material", description: "Direct instruction" },
    { startMinute: 20, endMinute: 35, title: "Practice", description: "Student exercises" },
    { startMinute: 35, endMinute: 42, title: "Group Discussion", description: "Pair review" },
    { startMinute: 42, endMinute: 45, title: "Wrap-up", description: "Summary and homework" },
  ];
}

function fmt(min: number) {
  return String(min).padStart(2, "0") + ":00";
}

export default function LessonPlanInput({ onPlanReady, onRunSimulation, simulationStatus }: Props) {
  const [text, setText] = useState("");
  const [plan, setPlan] = useState<LessonPlan | null >(null);
  const [structuring, setStructuring] = useState(false);

  async function handleStructure() {
    if (!text.trim()) return;
    setStructuring(true);
    // TODO: replace with real LLM API call
    await new Promise<void >((r) => setTimeout(r, 800));
    const segments = mockStructure(text);
    const newPlan: LessonPlan = { rawText: text, segments };
    setPlan(newPlan);
    onPlanReady(newPlan);
    setStructuring(false);
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-bold text-gray-800"> Lesson Plan </h2>

      <textarea
        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-700 resize-none focus:outline-none focus:ring-2 focus:ring-amber-400"
        rows={6}
        placeholder="Describe your 45-minute lesson..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={simulationStatus === "running"}
      />

      <button
        onClick={handleStructure}
        disabled={!text.trim() || structuring || simulationStatus === "running"}
        className="self-start rounded-lg bg-amber-500 px-5 py-2 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {structuring ? "Structuring…" : "Structure with AI"}
      </button>

      {plan && (
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Structured Plan
          </div>
          <ol className="divide-y divide-gray-100">
            {plan.segments.map((seg, i) => (
              <li key={i} className="flex items-start gap-3 px-4 py-3">
                <span className="mt-0.5 shrink-0 rounded bg-amber-100 px-2 py-0.5 text-xs font-mono text-amber-800">
                  {fmt(seg.startMinute)} – {fmt(seg.endMinute)}
                </span>
                <div >
                  <p className="text-sm font-semibold text-gray-800">{seg.title}</p>
                  <p className="text-xs text-gray-500">{seg.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {plan && simulationStatus === "idle" && (
        <button
          onClick={onRunSimulation}
          className="self-start rounded-lg bg-green-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-green-700 transition-colors"
        >
          Run Simulation
        </button>
      )}

      {simulationStatus === "running" && (
        <div className="flex items-center gap-2 text-sm text-green-700 font-medium">
          <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Simulation running…
        </div>
      )}

      {simulationStatus === "done" && (
        <p className="text-sm text-gray-600"> Simulation complete </p>
      )}
    </div>
  );
}
