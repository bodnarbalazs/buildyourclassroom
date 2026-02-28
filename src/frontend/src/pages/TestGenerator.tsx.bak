import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { notifyUnauthorized } from "../api/unauthorizedBus";

type Difficulty = "easy" | "medium" | "hard";
type QuestionType = "multiple-choice" | "true-false" | "short-answer" | "essay";

const QUESTION_TYPES: { value: QuestionType; label: string }[] = [
  { value: "multiple-choice", label: "Multiple Choice" },
  { value: "true-false", label: "True / False" },
  { value: "short-answer", label: "Short Answer" },
  { value: "essay", label: "Essay" },
];

export default function TestGenerator() {
  const { isAuthenticated } = useAuth();

  const [subject, setSubject] = useState("");
  const [questionCount, setQuestionCount] = useState(5);
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [selectedTypes, setSelectedTypes] = useState<Set<QuestionType>>(
    new Set(["multiple-choice"]),
  );
  const [generated, setGenerated] = useState(false);

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

  function toggleType(type: QuestionType) {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    // TODO: POST to backend API for AI-powered generation
    setGenerated(true);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col gap-8">
      <h1 className="text-3xl font-bold text-gray-900">Test Generator</h1>

      <form
        onSubmit={handleGenerate}
        className="rounded-xl border border-gray-200 bg-gray-50 p-6 flex flex-col gap-5 max-w-2xl"
      >
        {/* Subject */}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Subject / Topic</span>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="e.g. Photosynthesis"
            required
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </label>

        {/* Number of questions */}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Number of Questions</span>
          <input
            type="number"
            min={1}
            max={50}
            value={questionCount}
            onChange={(e) => setQuestionCount(Number(e.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </label>

        {/* Difficulty */}
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Difficulty</span>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value as Difficulty)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>

        {/* Question types */}
        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium text-gray-700">Question Types</legend>
          <div className="flex flex-wrap gap-4 mt-1">
            {QUESTION_TYPES.map(({ value, label }) => (
              <label key={value} className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={selectedTypes.has(value)}
                  onChange={() => toggleType(value)}
                  className="rounded border-gray-300"
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={selectedTypes.size === 0}
          className="self-start rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Generate Test
        </button>
      </form>

      {/* Placeholder results */}
      {generated && (
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Generated Test</h2>
          <p className="text-gray-500 text-sm">
            Test generation will be connected to the backend API. Parameters: {questionCount}{" "}
            {difficulty} question(s) on &ldquo;{subject}&rdquo; ({[...selectedTypes].join(", ")}).
          </p>
        </div>
      )}
    </div>
  );
}
