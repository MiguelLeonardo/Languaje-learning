/**
 * Typed API client for the SpeakFlow FastAPI backend (see backend/openapi.json).
 */

export type CEFR = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
export type ExerciseType = "shadowing" | "recall" | "guided" | "completion";
export type SupportLevel = "full" | "partial" | "low";

export interface GlossaryEntry {
  word: string;
  meaning: string;
  ipa?: string | null;
}

export interface ExercisePrompt {
  instruction_es: string;
  display_text?: string | null;
  translation?: string | null;
  glossary: GlossaryEntry[];
  visual_hint?: string | null;
  audio_text?: string | null;
  focus_words: string[];
}

export interface Exercise {
  id: string;
  type: ExerciseType;
  support: SupportLevel;
  scenario_id: string;
  phrase_id: string;
  prompt: ExercisePrompt;
  expected_text: string;
  pass_threshold: number;
  response_mode: "speech";
}

export interface LessonStage {
  type: ExerciseType;
  support: SupportLevel;
  exercises: Exercise[];
}

export interface LessonPlan {
  scenario_id: string;
  title: string;
  cefr: CEFR;
  stages: LessonStage[];
  roleplay_available: boolean;
}

export class SpeakFlowApiClient {
  constructor(
    private readonly baseUrl: string,
    private token: string | null = null,
  ) {}

  setToken(token: string) {
    this.token = token;
  }

  private headers(): Record<string, string> {
    return this.token ? { Authorization: `Bearer ${this.token}` } : {};
  }

  async getScenarios(cefr?: CEFR) {
    const q = cefr ? `?cefr=${cefr}` : "";
    const res = await fetch(`${this.baseUrl}/v1/scenarios${q}`, { headers: this.headers() });
    return res.json();
  }

  async getLesson(scenarioId: string): Promise<LessonPlan> {
    const res = await fetch(`${this.baseUrl}/v1/lessons/${scenarioId}`, { headers: this.headers() });
    return res.json();
  }

  async submitAudioAttempt(exerciseId: string, audioUri: string, mimeType = "audio/m4a") {
    const form = new FormData();
    form.append("audio", { uri: audioUri, name: "speech.m4a", type: mimeType } as unknown as Blob);
    const res = await fetch(`${this.baseUrl}/v1/exercises/${exerciseId}/attempts`, {
      method: "POST",
      headers: this.headers(),
      body: form,
    });
    return res.json();
  }
}
