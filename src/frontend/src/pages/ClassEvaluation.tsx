import { useEffect, useRef, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { notifyUnauthorized } from "../api/unauthorizedBus";

type StudentMetric = {
  id: number;
  name: string;
  attention: number;
  engagement: number;
};

const MOCK_STUDENTS: StudentMetric[] = Array.from({ length: 20 }, (_, i) => ({
  id: i,
  name: `Student ${i + 1}`,
  attention: Math.round(Math.random() * 100),
  engagement: Math.round(Math.random() * 100),
}));

export default function ClassEvaluation() {
  const { isAuthenticated } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [streaming, setStreaming] = useState(false);
  const [students] = useState<StudentMetric[]>(MOCK_STUDENTS);

  useEffect(() => {
    if (!isAuthenticated) notifyUnauthorized();
  }, [isAuthenticated]);

  useEffect(() => {
    if (!streaming) return;
    let cancelled = false;

    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        if (cancelled || !videoRef.current) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        videoRef.current.srcObject = stream;
      })
      .catch(() => setStreaming(false));

    return () => {
      cancelled = true;
      const src = videoRef.current?.srcObject as MediaStream | null;
      src?.getTracks().forEach((t) => t.stop());
    };
  }, [streaming]);

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-gray-500">Please log in to access Class Evaluation.</p>
      </div>
    );
  }

  const avgAttention = Math.round(
    students.reduce((s, st) => s + st.attention, 0) / students.length,
  );
  const avgEngagement = Math.round(
    students.reduce((s, st) => s + st.engagement, 0) / students.length,
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col gap-8">
      <h1 className="text-3xl font-bold text-gray-900">Class Evaluation</h1>

      <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6 items-start">
        {/* Video feed */}
        <div className="rounded-xl border border-gray-200 bg-black aspect-video flex items-center justify-center overflow-hidden">
          {streaming ? (
            <video ref={videoRef} autoPlay muted className="w-full h-full object-cover" />
          ) : (
            <div className="flex flex-col items-center gap-4">
              <svg className="w-16 h-16 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9A2.25 2.25 0 0 0 13.5 5.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
              <button
                onClick={() => setStreaming(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Start Camera
              </button>
            </div>
          )}
        </div>

        {/* Metrics panel */}
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-6 flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-gray-900">Real-Time Metrics</h2>
          <Metric label="Avg Attention" value={avgAttention} />
          <Metric label="Avg Engagement" value={avgEngagement} />
          <Metric label="Students Detected" value={students.length} max={students.length} />
          {streaming && (
            <button
              onClick={() => setStreaming(false)}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Stop Camera
            </button>
          )}
        </div>
      </div>

      {/* Student grid */}
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Student Overview</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
          {students.map((s) => (
            <div
              key={s.id}
              className="rounded-lg border border-gray-200 bg-white p-3 text-center"
            >
              <p className="text-sm font-medium text-gray-800">{s.name}</p>
              <p className="text-xs text-gray-500 mt-1">
                Att: {s.attention}% &middot; Eng: {s.engagement}%
              </p>
              <div
                className="mt-2 h-1.5 rounded-full"
                style={{
                  background: `linear-gradient(90deg, #3b82f6 ${s.attention}%, #e5e7eb ${s.attention}%)`,
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-900">{value}{max === 100 ? "%" : ""}</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
