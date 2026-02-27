export type Emotion = "neutral" | "focused" | "bored" | "confused" | "excited" | "sleepy";

export interface StudentState {
  id: number; // 0-29
  emotion: Emotion;
  thought?: string;
}

export interface LessonSegment {
  startMinute: number;
  endMinute: number;
  title: string;
  description: string;
}

export interface LessonPlan {
  segments: LessonSegment[];
  rawText: string;
}

export type SimulationStatus = "idle" | "running" | "done";

export interface SimulationState {
  status: SimulationStatus;
  students: StudentState[];
  currentMinute: number;
}
