import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { notifyUnauthorized } from "../api/unauthorizedBus";
import { apiFetch } from "../api/apiClient";
import type { LessonPlan, SimulationResponse, SimulationState, TickSnapshot } from "../types/simulation";
import ClassroomView from "../components/classroom/ClassroomView";
import LessonPlanInput from "../components/classroom/LessonPlanInput";
import ResultsPanel from "../components/classroom/ResultsPanel";

const TICK_INTERVAL_MS = 400;

const INITIAL: SimulationState = { status: "idle", students: [], currentMinute: 0 };

export default function ClassroomBuilder() {
  const { isAuthenticated } = useAuth();
  const [plan, setPlan] = useState<LessonPlan | null>(null);
  const [simulation, setSimulation] = useState<SimulationState>(INITIAL);
  const [ticks, setTicks] = useState<TickSnapshot[]>([]);
  const ticksRef = useRef<TickSnapshot[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval>>(null);

  useEffect(() => {
    if (!isAuthenticated) notifyUnauthorized();
  }, [isAuthenticated]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const animateTicks = useCallback((ticks: TickSnapshot[]) => {
    ticksRef.current = ticks;
    let idx = 0;

    // Show initial state immediately
    const first = ticks[0];
    setSimulation({
      status: "running",
      currentMinute: first.cycle,
      students: first.students.map((s) => ({ id: s.id, emotion: s.emotion, engagement: s.engagement })),
    });

    timerRef.current = setInterval(() => {
      idx++;
      if (idx >= ticksRef.current.length) {
        if (timerRef.current) clearInterval(timerRef.current);
        setSimulation((prev) => ({ ...prev, status: "done" }));
        return;
      }
      const tick = ticksRef.current[idx];
      setSimulation({
        status: "running",
        currentMinute: tick.cycle,
        students: tick.students.map((s) => ({ id: s.id, emotion: s.emotion, engagement: s.engagement })),
      });
    }, TICK_INTERVAL_MS);
  }, []);

  async function handleRunSimulation() {
    if (!plan) return;

    setSimulation({ status: "running", students: [], currentMinute: 0 });

    try {
      const res = await apiFetch("/api/simulation/run", {
        method: "POST",
        body: JSON.stringify({
          ca_schedule: plan.caSchedule,
          rows: 5,
          cols: 6,
          cycles: 45,
        }),
      });

      if (!res.ok) {
        setSimulation(INITIAL);
        return;
      }

      const data: SimulationResponse = await res.json();
      setTicks(data.ticks);
      animateTicks(data.ticks);
    } catch {
      setSimulation(INITIAL);
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-gray-500"> Please log in to access the Classroom Builder. </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col gap-8">
      <h1 className="text-3xl font-bold text-gray-900"> Classroom Builder </h1>

      <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6 items-start">
        {/* Classroom graphic + results */}
        <div className="flex flex-col gap-6">
          <ClassroomView simulation={simulation} />

          {simulation.status !== "idle" && (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
              <ResultsPanel simulation={simulation} ticks={ticks} />
            </div>
          )}
        </div>

        {/* Lesson plan input */}
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
          <LessonPlanInput
            onPlanReady={setPlan}
            onRunSimulation={handleRunSimulation}
            simulationStatus={simulation.status}
          />
        </div>
      </div>
    </div>
  );
}
