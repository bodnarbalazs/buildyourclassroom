import { useEffect, useRef, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { notifyUnauthorized } from "../api/unauthorizedBus";

type Difficulty = "easy" | "medium" | "hard";
type TestType = "quick-quiz" | "chapter-test" | "midterm" | "final-exam";
type QuestionType = "multiple-choice" | "true-false" | "short-answer" | "essay";

const ACCEPTED_FILE_TYPES = ".txt,.pdf,.doc,.docx,.mp3,.wav,.mp4,.webm,.ogg";

const TEST_TYPES: { value: TestType; label: string; description: string }[] = [
  { value: "quick-quiz", label: "Quick Quiz", description: "5–10 min, few questions" },
  { value: "chapter-test", label: "Chapter Test", description: "20–30 min, one topic" },
  { value: "midterm", label: "Midterm Exam", description: "45–60 min, broad coverage" },
  { value: "final-exam", label: "Final Exam", description: "90+ min, comprehensive" },
];

const QUESTION_TYPES: { value: QuestionType; label: string }[] = [
  { value: "multiple-choice", label: "Multiple Choice" },
  { value: "true-false", label: "True / False" },
  { value: "short-answer", label: "Short Answer" },
  { value: "essay", label: "Essay" },
];

function fileIcon(file: File): string {
  if (file.type.startsWith("video/")) return "🎥";
  if (file.type.startsWith("audio/")) return "🎧";
  return "📄";
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function TestGenerator() {
  const { isAuthenticated } = useAuth();

  const [file, setFile] = useState<File | null>(null);
  const [testType, setTestType] = useState<TestType>("chapter-test");
  const [questionCount, setQuestionCount] = useState(10);
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [selectedQuestionTypes, setSelectedQuestionTypes] = useState<Set<QuestionType>>(
    new Set(["multiple-choice"]),
  );
  const [language, setLanguage] = useState("English");
  const [additionalInstructions, setAdditionalInstructions] = useState("");
  const [generated, setGenerated] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isAuthenticated) notifyUnauthorized();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-gray-500">Please log in to access the Test Generator.</p>
      </div>
    );
  }

  function toggleQuestionType(type: QuestionType) {
    setSelectedQuestionTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    // TODO: POST to backend API for AI-powered generation
    setGenerated(true);
  }

  const inputClass =
    "rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Test Generator</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload your class material and configure the test parameters below.
        </p>
      </div>

      <form
        onSubmit={handleGenerate}
        className="rounded-xl border border-gray-200 bg-gray-50 p-6 flex flex-col gap-6 max-w-2xl"
      >
        {/* ── File Upload ── */}
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Source Material</span>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 bg-white px-4 py-8 cursor-pointer hover:border-blue-400 hover:bg-blue-50/30 transition-colors"
          >
            {file ? (
              <div className="flex items-center gap-3">
                <span className="text-2xl">{fileIcon(file)}</span>
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-gray-900">{file.name}</span>
                  <span className="text-xs text-gray-500">{formatSize(file.size)}</span>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="ml-2 rounded p-1 text-gray-400 hover:text-red-500 hover:bg-red-50"
                >
                  ✕
                </button>
              </div>
            ) : (
              <>
                <span className="text-3xl text-gray-400">⬆</span>
                <p className="text-sm text-gray-600">
                  <span className="font-medium text-blue-600">Click to upload</span> or drag & drop
                </p>
                <p className="text-xs text-gray-400">
                  Text files (.txt, .pdf, .docx) or recordings (.mp3, .wav, .mp4)
                </p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_FILE_TYPES}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="hidden"
          />
        </div>

        {/* ── Test Type ── */}
        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium text-gray-700">Test Type</legend>
          <div className="grid grid-cols-2 gap-2 mt-1">
            {TEST_TYPES.map(({ value, label, description }) => (
              <label
                key={value}
                className={`flex flex-col rounded-lg border px-3 py-2 cursor-pointer transition-colors ${
                  testType === value
                    ? "border-blue-500 bg-blue-50 ring-1 ring-blue-500"
                    : "border-gray-200 bg-white hover:border-gray-300"
                }`}
              >
                <input
                  type="radio"
                  name="testType"
                  value={value}
                  checked={testType === value}
                  onChange={() => setTestType(value)}
                  className="sr-only"
                />
                <span className="text-sm font-medium text-gray-900">{label}</span>
                <span className="text-xs text-gray-500">{description}</span>
              </label>
            ))}
          </div>
        </fieldset>

        {/* ── Difficulty ── */}
        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium text-gray-700">Difficulty</legend>
          <div className="flex gap-2 mt-1">
            {(["easy", "medium", "hard"] as Difficulty[]).map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setDifficulty(level)}
                className={`rounded-lg px-4 py-1.5 text-sm font-medium capitalize transition-colors ${
                  difficulty === level
                    ? "bg-blue-600 text-white"
                    : "border border-gray-200 bg-white text-gray-700 hover:border-gray-300"
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </fieldset>

        {/* ── Number of Questions ── */}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Number of Questions</span>
          <input
            type="number"
            min={1}
            max={100}
            value={questionCount}
            onChange={(e) => setQuestionCount(Number(e.target.value))}
            className={`${inputClass} w-24`}
          />
        </label>

        {/* ── Question Types ── */}
        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium text-gray-700">Question Types</legend>
          <div className="flex flex-wrap gap-4 mt-1">
            {QUESTION_TYPES.map(({ value, label }) => (
              <label key={value} className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={selectedQuestionTypes.has(value)}
                  onChange={() => toggleQuestionType(value)}
                  className="rounded border-gray-300"
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        {/* ── Language ── */}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Language</span>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className={`${inputClass} w-40`}
          >
            <option value="English">English</option>
            <option value="Hungarian">Hungarian</option>
            <option value="German">German</option>
            <option value="Spanish">Spanish</option>
            <option value="French">French</option>
          </select>
        </label>

        {/* ── Additional Instructions ── */}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">
            Additional Instructions <span className="font-normal text-gray-400">(optional)</span>
          </span>
          <textarea
            rows={3}
            value={additionalInstructions}
            onChange={(e) => setAdditionalInstructions(e.target.value)}
            placeholder="e.g. Focus on chapter 5, avoid questions about dates…"
            className={`${inputClass} resize-none`}
          />
        </label>

        {/* ── Submit ── */}
        <button
          type="submit"
          disabled={!file || selectedQuestionTypes.size === 0}
          className="self-start rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Generate Test
        </button>
      </form>

      {/* ── Placeholder Results ── */}
      {generated && (
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-6 max-w-2xl">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Generated Test</h2>
          <p className="text-gray-500 text-sm">
            Test generation will be connected to the backend API. Parameters: {questionCount}{" "}
            {difficulty} {testType} question(s) using &ldquo;{file?.name}&rdquo; (
            {[...selectedQuestionTypes].join(", ")}), language: {language}.
          </p>
        </div>
      )}
    </div>
  );
}
