import type { Assessment, Question } from "./types";
import { generatePdf } from "./generate-pdf";

function QuestionView({ question, number }: { question: Question; number: number }) {
  return (
    <div className="flex flex-col gap-1.5">
      <p className="text-sm font-medium text-gray-900">
        {number}. {question.question_text}
      </p>

      {question.question_type === "multiple-choice" && (
        <div className="flex flex-col gap-1 ml-5">
          {question.options.map((opt, i) => (
            <p
              key={i}
              className={`text-sm ${opt === question.correct_answer ? "font-semibold text-green-700" : "text-gray-700"}`}
            >
              {String.fromCharCode(65 + i)}) {opt}
            </p>
          ))}
        </div>
      )}

      {question.question_type === "true-false" && (
        <p className="text-sm ml-5 text-green-700 font-semibold">
          {question.correct_answer ? "True" : "False"}
        </p>
      )}

      {question.question_type === "short-answer" && (
        <p className="text-sm ml-5 text-green-700 font-semibold">{question.correct_answer}</p>
      )}

      {question.question_type === "essay" && (
        <p className="text-sm ml-5 text-green-700 italic">{question.correct_answer}</p>
      )}

      <div className="flex gap-2 ml-5 mt-0.5">
        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 capitalize">
          {question.difficulty}
        </span>
        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
          {question.question_type}
        </span>
      </div>

      {question.explanation && (
        <p className="text-xs text-gray-500 ml-5 italic">{question.explanation}</p>
      )}
    </div>
  );
}

export default function AssessmentView({ assessment }: { assessment: Assessment }) {
  let questionNum = 0;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{assessment.title}</h2>
          <div className="flex gap-3 mt-1 text-xs text-gray-500">
            <span>Subject: {assessment.subject}</span>
            <span>{assessment.total_questions} questions</span>
            {"total_points" in assessment && <span>{assessment.total_points} points</span>}
            {"time_limit_minutes" in assessment && (
              <span>{assessment.time_limit_minutes} min</span>
            )}
          </div>
        </div>
        <button
          onClick={() => generatePdf(assessment)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Download PDF
        </button>
      </div>

      {"sections" in assessment ? (
        assessment.sections.map((section, si) => (
          <div key={si} className="flex flex-col gap-3">
            <h3 className="text-base font-semibold text-gray-800 border-b border-gray-200 pb-1">
              {section.section_title}
            </h3>
            {section.questions.map((q) => {
              questionNum++;
              return (
                <div key={questionNum} className="flex flex-col gap-1">
                  <QuestionView question={q.base} number={questionNum} />
                  <div className="flex gap-2 ml-5">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-purple-50 text-purple-600">
                      {q.bloom_level}
                    </span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">
                      {q.topic_tag}
                    </span>
                    {"points" in q && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">
                        {q.points} pts
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ))
      ) : (
        <div className="flex flex-col gap-4">
          {assessment.questions.map((q) => {
            questionNum++;
            return <QuestionView key={questionNum} question={q} number={questionNum} />;
          })}
        </div>
      )}
    </div>
  );
}
