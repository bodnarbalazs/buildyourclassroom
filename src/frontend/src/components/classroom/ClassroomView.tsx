import type { Emotion, SimulationState, StudentState } from "../../types/simulation";
import StudentFace, { EMOTION_COLORS } from "./StudentFace";
import ThoughtBubble from "./ThoughtBubble";

// 3 cols x 5 rows = 15 desks, 2 per desk = 30 students.
const IDLE_EMOTIONS: Emotion[] = [
  "passive",    "engaged",    "confused",   "passive",    "engaged",    "anxious",
  "engaged",    "passive",    "engaged",    "confused",   "passive",    "engaged",
  "passive",    "disruptive", "passive",    "engaged",    "anxious",    "engaged",
  "anxious",    "passive",    "engaged",    "passive",    "passive",    "confused",
  "engaged",    "passive",    "passive",    "engaged",    "disruptive", "passive",
];

interface Props {
  simulation: SimulationState;
}

function StudentSeat({ student }: { student: StudentState }) {
  const glowColor = EMOTION_COLORS[student.emotion];
  return (
    <div className="relative flex flex-col items-center">
      {student.thought && <ThoughtBubble text={student.thought} />}
      <div className="relative">
        <div
          className="absolute inset-[-15%] rounded-full"
          style={{
            background: `radial-gradient(circle at 50% 42%, ${glowColor}cc 0%, ${glowColor}80 35%, ${glowColor}30 55%, transparent 72%)`,
            filter: "blur(2px)",
          }}
        />
        <StudentFace emotion={student.emotion} studentId={student.id} className="relative w-full h-auto" />
      </div>
    </div>
  );
}

function Desk({ left, right }: { left: StudentState; right: StudentState }) {
  return (
    <div className="flex flex-col items-stretch gap-1.5">
      {/* Students sitting behind the desk */}
      <div className="grid grid-cols-2 gap-3 px-1">
        <StudentSeat student={left} />
        <StudentSeat student={right} />
      </div>
      {/* Desk surface (top-down view) */}
      <div
        className="rounded-lg border border-amber-700/30 h-6"
        style={{
          background: "linear-gradient(180deg, #d4a574 0%, #c08a52 50%, #b07a42 100%)",
          boxShadow: "0 2px 6px rgba(100,60,10,0.25), inset 0 1px 0 rgba(255,255,255,0.2)",
        }}
      />
    </div>
  );
}

export default function ClassroomView({ simulation }: Props) {
  const all: StudentState[] = Array.from({ length: 30 }, (_, i) =>
    simulation.students.find((s) => s.id === i) ?? { id: i, emotion: IDLE_EMOTIONS[i] }
  );

  return (
    <div className="w-full rounded-xl border-2 border-stone-400/60 overflow-hidden shadow-lg">
      {/* Wall with blackboard */}
      <div
        className="px-3 md:px-6 pt-5 pb-4"
        style={{
          background: "linear-gradient(180deg, #6b6560 0%, #8c8580 60%, #9e9690 100%)",
          borderBottom: "3px solid #78716c",
        }}
      >
        <div
          className="rounded border-[5px] border-amber-900/80 flex items-center justify-center mx-auto py-5 max-w-[380px] w-full"
          style={{
            background: "linear-gradient(145deg, #1a5c2e 0%, #14532d 40%, #1e4a30 100%)",
            boxShadow: "inset 0 2px 12px rgba(0,0,0,0.4), 0 4px 8px rgba(0,0,0,0.2)",
          }}
        >
          <span className="text-green-300/40 font-mono text-xs tracking-[0.25em] select-none">
            TODAY'S LESSON
          </span>
        </div>
      </div>

      {/* Classroom floor area */}
      <div
        className="px-3 md:px-6 pb-8 pt-5 overflow-hidden"
        style={{
          background: `
            repeating-conic-gradient(#efe3d4 0% 25%, #e8dbc9 0% 50%) 0 0 / 48px 48px
          `,
        }}
      >
        {/* Teacher's desk */}
        <div className="flex justify-center mb-6">
          <div
            className="rounded-lg px-10 py-2.5 text-xs font-bold tracking-[0.2em] uppercase border border-amber-800/40"
            style={{
              background: "linear-gradient(180deg, #c49058 0%, #a67540 100%)",
              boxShadow: "0 3px 8px rgba(100,55,10,0.3), inset 0 1px 0 rgba(255,255,255,0.15)",
              color: "#4a2c12",
            }}
          >
            Teacher
          </div>
        </div>

        {/* Student desks grid — fills available width */}
        <div className="flex flex-col gap-2 md:gap-4 w-full max-w-xl mx-auto">
          {Array.from({ length: 5 }, (_, row) => (
            <div key={row} className="grid grid-cols-3 gap-2 md:gap-4">
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
  );
}
