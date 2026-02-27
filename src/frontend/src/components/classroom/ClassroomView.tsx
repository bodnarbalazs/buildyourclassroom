import type { Emotion, SimulationState, StudentState } from "../../types/simulation";
import StudentFace from "./StudentFace";
import ThoughtBubble from "./ThoughtBubble";

// 3 cols x 5 rows = 15 desks, 2 per desk = 30 students.
const IDLE_EMOTIONS: Emotion[] = [
  "neutral",  "focused",  "bored",   "confused", "excited",  "sleepy",
  "focused",  "neutral",  "excited", "bored",    "sleepy",   "confused",
  "confused", "excited",  "neutral", "sleepy",   "bored",    "focused",
  "sleepy",   "bored",    "focused", "excited",  "neutral",  "confused",
  "excited",  "confused", "sleepy",  "neutral",  "focused",  "bored",
];
// IDs: row r, col c: left = r*6+c*2, right = r*6+c*2+1

interface Props {
  simulation: SimulationState;
}

function Desk({ left, right }: { left: StudentState; right: StudentState }) {
  return (
    <div className="flex flex-col items-stretch">
      <div
        className="relative flex items-end justify-around px-2 pt-2 pb-1 bg-amber-200 border-2 border-amber-700 rounded-t"
        style={{ boxShadow: "inset 0 -2px 0 #b45309" }}
      >
        <div className="relative flex flex-col items-center">
          {left.thought && <ThoughtBubble text={left.thought} />}
          <StudentFace emotion={left.emotion} size={34} />
        </div>
        <div className="w-5 h-3 rounded-sm bg-sky-200 border border-sky-400 opacity-70 mb-1" />
        <div className="relative flex flex-col items-center">
          {right.thought && <ThoughtBubble text={right.thought} />}
          <StudentFace emotion={right.emotion} size={34} />
        </div>
      </div>
      <div className="h-3 bg-amber-700 rounded-b border-x-2 border-b-2 border-amber-800" />
    </div>
  );
}

export default function ClassroomView({ simulation }: Props) {
  const all: StudentState[] = Array.from({ length: 30 }, (_, i) =>
    simulation.students.find((s) => s.id === i) ?? { id: i, emotion: IDLE_EMOTIONS[i] }
  );

  return (
    <div className="w-full rounded-xl border-2 border-amber-800 overflow-hidden">
      <div className="bg-amber-900 px-8 pt-5 pb-3">
        <div
          className="bg-green-800 border-4 border-amber-600 rounded flex items-center justify-center mx-auto"
          style={{ height: 72, maxWidth: 560 }}
        >
          <span className="text-white/60 font-mono text-sm tracking-widest select-none">
            — Today’s Lesson —
          </span>
        </div>
      </div>
      <div className="px-6 pb-8 pt-4 bg-amber-50" style={{ perspective: 700 }}>
        <div style={{ transform: "rotateX(10deg)", transformOrigin: "top center" }}>
          <div className="flex justify-center mb-6">
            <div
              className="bg-amber-300 border-2 border-amber-700 rounded px-10 py-1.5 text-xs font-semibold text-amber-900 tracking-widest uppercase"
              style={{ boxShadow: "0 5px 0 #b45309" }}
            >
              Teacher
            </div>
          </div>
          <div className="flex flex-col gap-5">
            {Array.from({ length: 5 }, (_, row) => (
              <div key={row} className="grid grid-cols-3 gap-4">
                {Array.from({ length: 3 }, (_, col) => (
                  <Desk
                    key={col}
                    left={all[row * 6 + col * 2]}
                    right={all[row * 6 + col * 2 + 1]}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
