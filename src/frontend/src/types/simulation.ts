export type Emotion = "engaged" | "passive" | "anxious" | "confused" | "disruptive";

export interface StudentState {
  id: number;
  emotion: Emotion;
  engagement?: number;
  thought?: string;
}

export interface LessonSegment {
  startMinute: number;
  endMinute: number;
  title: string;
  description: string;
}

export interface ScheduleEvent {
  time: number;
  action: number;
  duration?: number;
}

export interface LessonPlan {
  segments: LessonSegment[];
  caSchedule: ScheduleEvent[];
  rawText: string;
}

export type SimulationStatus = "idle" | "running" | "done";

export interface SimulationState {
  status: SimulationStatus;
  students: StudentState[];
  currentMinute: number;
}

export interface TickSnapshot {
  cycle: number;
  students: { id: number; engagement: number; emotion: Emotion }[];
  avg_engagement: number;
}

export interface SimulationResponse {
  rows: number;
  cols: number;
  cycles: number;
  max_engagement: number;
  ticks: TickSnapshot[];
}
