export type Emotion = "engaged" | "passive" | "anxious" | "confused" | "disruptive";

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
