export type Difficulty = "easy" | "medium" | "hard";
export type BloomLevel = "remember" | "understand" | "apply" | "analyze";

interface BaseQuestion {
  question_text: string;
  explanation: string;
  difficulty: Difficulty;
}

export interface MultipleChoiceQuestion extends BaseQuestion {
  question_type: "multiple-choice";
  options: string[];
  correct_answer: string;
}

export interface TrueFalseQuestion extends BaseQuestion {
  question_type: "true-false";
  correct_answer: boolean;
}

export interface ShortAnswerQuestion extends BaseQuestion {
  question_type: "short-answer";
  correct_answer: string;
}

export interface EssayQuestion extends BaseQuestion {
  question_type: "essay";
  correct_answer: string;
  grading_rubric: string[];
}

export type Question = MultipleChoiceQuestion | TrueFalseQuestion | ShortAnswerQuestion | EssayQuestion;

interface AssessmentBase {
  title: string;
  subject: string;
  generated_from: string;
  assessment_type: string;
  total_questions: number;
  created_at: string;
}

export interface Quiz extends AssessmentBase {
  questions: Question[];
}

interface PracticeTestSection {
  section_title: string;
  questions: { base: Question; topic_tag: string; bloom_level: BloomLevel }[];
}

export interface PracticeTest extends AssessmentBase {
  sections: PracticeTestSection[];
}

interface ExamSection {
  section_title: string;
  questions: { base: Question; topic_tag: string; bloom_level: BloomLevel; points: number }[];
}

export interface Exam extends AssessmentBase {
  sections: ExamSection[];
  total_points: number;
  time_limit_minutes: number;
}

export type Assessment = Quiz | PracticeTest | Exam;

export interface AssessmentResult {
  transcript_summary: string;
  assessment: Assessment;
}
