import jsPDF from "jspdf";
import type { Assessment, Question } from "./types";

const PAGE_WIDTH = 210;
const MARGIN = 20;
const CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN;
const LINE_HEIGHT = 6;
const FONT_SIZE = {
  title: 18,
  sectionHeader: 14,
  body: 11,
  small: 9,
} as const;

function ensureSpace(doc: jsPDF, y: number, needed: number): number {
  if (y + needed > doc.internal.pageSize.getHeight() - MARGIN) {
    doc.addPage();
    return MARGIN;
  }
  return y;
}

function drawText(
  doc: jsPDF,
  text: string,
  x: number,
  y: number,
  fontSize: number,
  style: "normal" | "bold" = "normal",
): number {
  doc.setFontSize(fontSize);
  doc.setFont("helvetica", style);
  const lines = doc.splitTextToSize(text, CONTENT_WIDTH - (x - MARGIN));
  const totalHeight = lines.length * (fontSize * 0.4 + 1);
  y = ensureSpace(doc, y, totalHeight);
  doc.text(lines, x, y);
  return y + totalHeight;
}

function renderQuestion(doc: jsPDF, q: Question, num: number, y: number): number {
  y = ensureSpace(doc, y, 20);
  y = drawText(doc, `${num}. ${q.question_text}`, MARGIN, y, FONT_SIZE.body, "bold");

  switch (q.question_type) {
    case "multiple-choice":
      for (let i = 0; i < q.options.length; i++) {
        y = ensureSpace(doc, y, LINE_HEIGHT);
        y = drawText(
          doc,
          `${String.fromCharCode(65 + i)}) ${q.options[i]}`,
          MARGIN + 8,
          y,
          FONT_SIZE.body,
        );
      }
      break;
    case "true-false":
      y = ensureSpace(doc, y, LINE_HEIGHT);
      y = drawText(doc, "True  /  False", MARGIN + 8, y, FONT_SIZE.body);
      break;
    case "short-answer":
      y = ensureSpace(doc, y, LINE_HEIGHT + 4);
      doc.setDrawColor(180);
      doc.line(MARGIN + 8, y + 2, MARGIN + CONTENT_WIDTH - 8, y + 2);
      y += LINE_HEIGHT + 2;
      break;
    case "essay":
      for (let i = 0; i < 4; i++) {
        y = ensureSpace(doc, y, LINE_HEIGHT);
        doc.setDrawColor(210);
        doc.line(MARGIN + 8, y + 2, MARGIN + CONTENT_WIDTH - 8, y + 2);
        y += LINE_HEIGHT;
      }
      break;
  }

  return y;
}

export function generatePdf(assessment: Assessment): void {
  const doc = new jsPDF();
  let y = MARGIN;

  // Header
  y = drawText(doc, assessment.title, MARGIN, y, FONT_SIZE.title, "bold");
  y += 2;

  const meta = [
    `Subject: ${assessment.subject}`,
    `Type: ${assessment.assessment_type}`,
    `Questions: ${assessment.total_questions}`,
  ];
  if ("total_points" in assessment) meta.push(`Total Points: ${assessment.total_points}`);
  if ("time_limit_minutes" in assessment)
    meta.push(`Time Limit: ${assessment.time_limit_minutes} min`);

  doc.setTextColor(100);
  y = drawText(doc, meta.join("  |  "), MARGIN, y, FONT_SIZE.small);
  doc.setTextColor(0);
  y += 4;

  doc.setDrawColor(200);
  doc.line(MARGIN, y, PAGE_WIDTH - MARGIN, y);
  y += 6;

  // Questions
  let questionNum = 1;

  if ("sections" in assessment) {
    for (const section of assessment.sections) {
      y = ensureSpace(doc, y, 20);
      y = drawText(doc, section.section_title, MARGIN, y, FONT_SIZE.sectionHeader, "bold");
      y += 2;

      for (const q of section.questions) {
        y = renderQuestion(doc, q.base, questionNum, y);
        if ("points" in q) {
          doc.setFontSize(FONT_SIZE.small);
          doc.setFont("helvetica", "italic");
          doc.setTextColor(100);
          y = ensureSpace(doc, y, LINE_HEIGHT);
          doc.text(`[${q.points} pts]`, MARGIN + 4, y);
          doc.setTextColor(0);
          y += LINE_HEIGHT;
        }
        y += 4;
        questionNum++;
      }
    }
  } else {
    for (const q of assessment.questions) {
      y = renderQuestion(doc, q, questionNum, y);
      y += 4;
      questionNum++;
    }
  }

  // Answer key on new page
  doc.addPage();
  y = MARGIN;
  y = drawText(doc, "Answer Key", MARGIN, y, FONT_SIZE.title, "bold");
  y += 4;

  questionNum = 1;
  const allQuestions: Question[] =
    "sections" in assessment
      ? assessment.sections.flatMap((s) => s.questions.map((q) => q.base))
      : assessment.questions;

  for (const q of allQuestions) {
    y = ensureSpace(doc, y, 16);
    const answer =
      q.question_type === "true-false"
        ? q.correct_answer
          ? "True"
          : "False"
        : String(q.correct_answer);
    y = drawText(doc, `${questionNum}. ${answer}`, MARGIN, y, FONT_SIZE.body, "bold");
    if (q.explanation) {
      y = drawText(doc, q.explanation, MARGIN + 6, y, FONT_SIZE.small);
    }
    y += 2;
    questionNum++;
  }

  const filename = assessment.title.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase();
  doc.save(`${filename}.pdf`);
}
