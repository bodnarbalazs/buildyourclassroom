import { useState } from "react";
import { apiFetch } from "../../api/apiClient";
import type { LessonPlan, LessonSegment, ScheduleEvent } from "../../types/simulation";

interface Props {
  onPlanReady: (plan: LessonPlan) => void;
  onRunSimulation: () => void;
  simulationStatus: "idle" | "running" | "done";
}

interface SectionElement {
  element_type: string;
  ca_action: number;
  pedagogical_rationale: string;
  key_points?: string[];
  instructor_notes?: string;
  focus_area?: string;
  questions?: string[];
  activity_title?: string;
  instructions?: string;
  group_size?: number;
  materials_needed?: string[];
  support_focus?: string;
  follow_up?: string;
  energizer_type?: string;
  description?: string;
  game_title?: string;
  rules?: string;
  team_based?: boolean;
}

interface AgendaSection {
  order: number;
  title: string;
  description: string;
  start_minute: number;
  duration_minutes: number;
  learning_objectives: string[];
  element: SectionElement;
}

interface AgendaResponse {
  lesson_title: string;
  subject: string;
  target_audience: string;
  total_duration_minutes: number;
  overall_objectives: string[];
  sections: AgendaSection[];
  summary: string;
  ca_schedule: ScheduleEvent[];
}

const ELEMENT_LABELS: Record<string, { label: string; color: string }> = {
  LECTURE: { label: "Lecture", color: "bg-blue-100 text-blue-800" },
  TARGETED_CHECK: { label: "Targeted Check", color: "bg-violet-100 text-violet-800" },
  GROUP_ACTIVITY: { label: "Group Activity", color: "bg-emerald-100 text-emerald-800" },
  INDIVIDUAL_SUPPORT: { label: "Individual Support", color: "bg-rose-100 text-rose-800" },
  ENERGIZER: { label: "Energizer", color: "bg-yellow-100 text-yellow-800" },
  GAME_CHALLENGE: { label: "Game Challenge", color: "bg-orange-100 text-orange-800" },
};

function fmt(min: number) {
  return String(min).padStart(2, "0") + ":00";
}

function ElementDetails({ element }: { element: SectionElement }) {
  switch (element.element_type) {
    case "LECTURE":
      return (
        <>
          {element.key_points && element.key_points.length > 0 && (
            <div className="mt-1">
              <span className="text-xs font-medium text-gray-500">Key Points:</span>
              <ul className="list-disc list-inside text-xs text-gray-600 ml-1">
                {element.key_points.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          )}
          {element.instructor_notes && (
            <p className="text-xs text-gray-500 italic mt-1">{element.instructor_notes}</p>
          )}
        </>
      );
    case "TARGETED_CHECK":
      return (
        <>
          {element.focus_area && (
            <p className="text-xs text-gray-600 mt-1"><span className="font-medium text-gray-500">Focus:</span> {element.focus_area}</p>
          )}
          {element.questions && element.questions.length > 0 && (
            <div className="mt-1">
              <span className="text-xs font-medium text-gray-500">Questions:</span>
              <ul className="list-decimal list-inside text-xs text-gray-600 ml-1">
                {element.questions.map((q, i) => <li key={i}>{q}</li>)}
              </ul>
            </div>
          )}
        </>
      );
    case "GROUP_ACTIVITY":
      return (
        <>
          {element.activity_title && (
            <p className="text-xs text-gray-600 mt-1"><span className="font-medium text-gray-500">Activity:</span> {element.activity_title}</p>
          )}
          {element.instructions && (
            <p className="text-xs text-gray-600"><span className="font-medium text-gray-500">Instructions:</span> {element.instructions}</p>
          )}
          {element.group_size && (
            <p className="text-xs text-gray-600"><span className="font-medium text-gray-500">Group size:</span> {element.group_size}</p>
          )}
          {element.materials_needed && element.materials_needed.length > 0 && (
            <p className="text-xs text-gray-600"><span className="font-medium text-gray-500">Materials:</span> {element.materials_needed.join(", ")}</p>
          )}
        </>
      );
    case "INDIVIDUAL_SUPPORT":
      return (
        <>
          {element.support_focus && (
            <p className="text-xs text-gray-600 mt-1"><span className="font-medium text-gray-500">Focus:</span> {element.support_focus}</p>
          )}
          {element.follow_up && (
            <p className="text-xs text-gray-600"><span className="font-medium text-gray-500">Follow-up:</span> {element.follow_up}</p>
          )}
        </>
      );
    case "ENERGIZER":
      return (
        <>
          {element.energizer_type && (
            <p className="text-xs text-gray-600 mt-1"><span className="font-medium text-gray-500">Type:</span> {element.energizer_type.replace("_", " ")}</p>
          )}
          {element.description && (
            <p className="text-xs text-gray-600">{element.description}</p>
          )}
        </>
      );
    case "GAME_CHALLENGE":
      return (
        <>
          {element.game_title && (
            <p className="text-xs text-gray-600 mt-1"><span className="font-medium text-gray-500">Game:</span> {element.game_title}</p>
          )}
          {element.rules && (
            <p className="text-xs text-gray-600"><span className="font-medium text-gray-500">Rules:</span> {element.rules}</p>
          )}
          {element.team_based !== undefined && (
            <p className="text-xs text-gray-600"><span className="font-medium text-gray-500">Team-based:</span> {element.team_based ? "Yes" : "No"}</p>
          )}
        </>
      );
    default:
      return null;
  }
}

export default function LessonPlanInput({ onPlanReady, onRunSimulation, simulationStatus }: Props) {
  const [topic, setTopic] = useState("");
  const [subject, setSubject] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [duration, setDuration] = useState(45);
  const [additionalInstructions, setAdditionalInstructions] = useState("");

  const [plan, setPlan] = useState<LessonPlan | null>(null);
  const [agenda, setAgenda] = useState<AgendaResponse | null>(null);
  const [structuring, setStructuring] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const disabled = simulationStatus === "running";
  const inputClass =
    "rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-amber-400";

  async function handleStructure() {
    if (!topic.trim() || !subject.trim() || !targetAudience.trim()) return;
    setStructuring(true);
    setError(null);

    try {
      const res = await apiFetch("/api/agenda/generate", {
        method: "POST",
        body: JSON.stringify({
          subject: subject.trim(),
          topic: topic.trim(),
          target_audience: targetAudience.trim(),
          duration_minutes: duration,
          ...(additionalInstructions.trim() && { additional_instructions: additionalInstructions.trim() }),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Failed to generate lesson plan" }));
        throw new Error(err.detail ?? `Server error (${res.status})`);
      }

      const data: AgendaResponse = await res.json();
      setAgenda(data);

      const segments: LessonSegment[] = data.sections.map((s) => ({
        startMinute: s.start_minute,
        endMinute: s.start_minute + s.duration_minutes,
        title: s.title,
        description: s.description,
      }));

      const newPlan: LessonPlan = {
        rawText: topic,
        segments,
        caSchedule: data.ca_schedule,
      };
      setPlan(newPlan);
      onPlanReady(newPlan);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setStructuring(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-bold text-gray-800">Lesson Plan</h2>

      {/* Topic */}
      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium text-gray-700">Topic</span>
        <textarea
          className={`${inputClass} resize-none`}
          rows={4}
          placeholder="Describe what the lesson should cover..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={disabled}
        />
      </label>

      {/* Subject & Target Audience */}
      <div className="grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Subject</span>
          <input
            type="text"
            className={inputClass}
            placeholder="e.g. Biology, History"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={disabled}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Target Audience</span>
          <input
            type="text"
            className={inputClass}
            placeholder="e.g. 10th grade"
            value={targetAudience}
            onChange={(e) => setTargetAudience(e.target.value)}
            disabled={disabled}
          />
        </label>
      </div>

      {/* Duration */}
      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium text-gray-700">Duration (minutes)</span>
        <input
          type="number"
          min={1}
          max={180}
          className={`${inputClass} w-24`}
          value={duration}
          onChange={(e) => setDuration(Number(e.target.value))}
          disabled={disabled}
        />
      </label>

      {/* Additional Instructions */}
      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium text-gray-700">
          Additional Instructions <span className="font-normal text-gray-400">(optional)</span>
        </span>
        <textarea
          className={`${inputClass} resize-none`}
          rows={2}
          placeholder="e.g. Include a hands-on experiment, focus on visual learners..."
          value={additionalInstructions}
          onChange={(e) => setAdditionalInstructions(e.target.value)}
          disabled={disabled}
        />
      </label>

      <button
        onClick={handleStructure}
        disabled={!topic.trim() || !subject.trim() || !targetAudience.trim() || structuring || disabled}
        className="self-start rounded-lg bg-amber-500 px-5 py-2 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {structuring ? "Generating Lesson Plan…" : "Generate Lesson Plan"}
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Full Lesson Plan Display */}
      {agenda && plan && (
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 bg-amber-50 border-b border-gray-200">
            <h3 className="text-base font-bold text-gray-900">{agenda.lesson_title}</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {agenda.subject} &middot; {agenda.target_audience} &middot; {agenda.total_duration_minutes} min
            </p>
          </div>

          {/* Objectives */}
          {agenda.overall_objectives.length > 0 && (
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Objectives</p>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-0.5">
                {agenda.overall_objectives.map((obj, i) => <li key={i}>{obj}</li>)}
              </ul>
            </div>
          )}

          {/* Sections */}
          <ol className="divide-y divide-gray-100">
            {agenda.sections.map((section) => {
              const badge = ELEMENT_LABELS[section.element.element_type];
              return (
                <li key={section.order} className="px-4 py-3">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 shrink-0 rounded bg-amber-100 px-2 py-0.5 text-xs font-mono text-amber-800">
                      {fmt(section.start_minute)} – {fmt(section.start_minute + section.duration_minutes)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-semibold text-gray-800">{section.title}</p>
                        {badge && (
                          <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${badge.color}`}>
                            {badge.label}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">{section.description}</p>

                      {section.element.pedagogical_rationale && (
                        <p className="text-xs text-amber-700 mt-1 italic">
                          {section.element.pedagogical_rationale}
                        </p>
                      )}

                      <ElementDetails element={section.element} />

                      {section.learning_objectives.length > 0 && (
                        <div className="mt-1.5">
                          <span className="text-[10px] font-semibold text-gray-400 uppercase">Learning Objectives</span>
                          <ul className="list-disc list-inside text-xs text-gray-500">
                            {section.learning_objectives.map((lo, i) => <li key={i}>{lo}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>

          {/* Summary */}
          {agenda.summary && (
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Summary</p>
              <p className="text-sm text-gray-700">{agenda.summary}</p>
            </div>
          )}
        </div>
      )}

      {plan && (simulationStatus === "idle" || simulationStatus === "done") && (
        <button
          onClick={onRunSimulation}
          className="self-start rounded-lg bg-green-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-green-700 transition-colors"
        >
          {simulationStatus === "done" ? "Run Again" : "Run Simulation"}
        </button>
      )}

      {simulationStatus === "running" && (
        <div className="flex items-center gap-2 text-sm text-green-700 font-medium">
          <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Simulation running…
        </div>
      )}
    </div>
  );
}
