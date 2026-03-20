import type {
  UploadResponse,
  ExplainResponse,
  QuizResponse,
  CheckResponse,
  ChatMessage,
  ChatResponse,
  VideoGenerateResponse,
  VideoStatusResponse,
  SearchResponse,
} from "@/types";

const BASE = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/documents/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function getExplanation(
  sessionId: string,
  topicIndex: number
): Promise<ExplainResponse> {
  return request<ExplainResponse>("/teaching/explain", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, topic_index: topicIndex }),
  });
}

export async function getQuiz(
  sessionId: string,
  topicIndex: number,
  numQuestions = 5
): Promise<QuizResponse> {
  return request<QuizResponse>("/teaching/quiz", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      topic_index: topicIndex,
      num_questions: numQuestions,
    }),
  });
}

export async function checkAnswers(
  answers: { question: string; correct_answer: string; student_answer: string }[]
): Promise<CheckResponse> {
  return request<CheckResponse>("/teaching/check", {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export async function sendChat(
  sessionId: string,
  topicIndex: number,
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> {
  return request<ChatResponse>("/teaching/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      topic_index: topicIndex,
      message,
      history,
    }),
  });
}

export async function generateVideo(
  sessionId: string,
  topicIndex: number
): Promise<VideoGenerateResponse> {
  return request<VideoGenerateResponse>("/videos/generate", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, topic_index: topicIndex }),
  });
}

export async function getVideoStatus(
  jobId: string
): Promise<VideoStatusResponse> {
  return request<VideoStatusResponse>(`/videos/status/${jobId}`);
}

export async function searchIndustryStandards(
  topicTitle: string,
  topicContent: string
): Promise<SearchResponse> {
  return request<SearchResponse>("/search/industry-standards", {
    method: "POST",
    body: JSON.stringify({ topic_title: topicTitle, topic_content: topicContent }),
  });
}
