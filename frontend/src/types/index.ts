export interface Topic {
  index: number;
  title: string;
  content: string;
}

export interface UploadResponse {
  session_id: string;
  topics: Topic[];
}

export interface ExplainResponse {
  explanation: string;
}

export interface QuizItem {
  question: string;
  answer: string;
}

export interface QuizResponse {
  questions: QuizItem[];
}

export interface CheckResult {
  question: string;
  correct: boolean;
  explanation: string;
}

export interface CheckResponse {
  results: CheckResult[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
}

export interface VideoGenerateResponse {
  job_id: string;
  status: string;
}

export interface VideoStatusResponse {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  video_url: string | null;
  error: string | null;
}

export interface SourceLink {
  title: string;
  url: string;
  snippet: string;
}

export interface SearchResponse {
  summary: string;
  sources: SourceLink[];
}
