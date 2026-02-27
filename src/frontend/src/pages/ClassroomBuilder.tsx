import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { notifyUnauthorized } from "../api/unauthorizedBus";
import type { LessonPlan, SimulationState } from "../types/simulation";
import ClassroomView from "../components/classroom/ClassroomView";
import LessonPlanInput from "../components/classroom/LessonPlanInput";
import ResultsPanel from "../components/classroom/ResultsPanel";

const EMOTIONS = ["neutral", "focused", "bored", "confused", "excited", "sleepy"] as const;

const INITIAL: SimulationState = { status: "idle", students: [], currentMinute: 0 };

export default function ClassroomBuilder() {
  const { isAuthenticated } = useAuth();
  const [_plan, setPlan] = useState<LessonPlan | null >(null);
  const [simulation, setSimulation] = useState<SimulationState >(INITIAL);

  useEffect(() => {
    if (!isAuthenticated) notifyUnauthorized();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-gray-500"> Please log in to access the Classroom Builder. </p>
      </div>
    );
  }

  function handleRunSimulation() {
    // TODO: POST plan to API and open WebSocket/SSE stream
    // Mock: seed 30 students with random emotions to show the classroom alive
    setSimulation({
      status: "running",
      currentMinute: 0,
      students: Array.from({ length: 30 }, (_, i) => ({
        id: i,
        emotion: EMOTIONS[Math.floor(Math.random() * EMOTIONS.length)],
        thought: i === 3 ? "Hmm..." : i === 12 ? "I get it!" : undefined,
      })),
    });
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 flex flex-col gap-8">
      <h1 className="text-3xl font-bold text-gray-900"> Classroom Builder </h1>

      {/* 1. Classroom drawing */}
      <ClassroomView simulation={simulation} />

      {/* 2. Lesson plan input */}
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
        <LessonPlanInput
          onPlanReady={setPlan}
          onRunSimulation={handleRunSimulation}
          simulationStatus={simulation.status}
        />
      </div>

      {/* 3. Results -- only shown once simulation starts */}
      {simulation.status !== "idle" && (
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
          <ResultsPanel simulation={simulation} />
        </div>
      )}
    </div>
  );
}
