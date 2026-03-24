"use client";

import { useState } from "react";
import {
  Loader2,
  CheckCircle2,
  XCircle,
  ClipboardList,
  RefreshCw,
} from "lucide-react";
import { getQuiz, checkAnswers } from "@/lib/api";
import type { QuizItem, CheckResult } from "@/types";

interface QuizProps {
  sessionId: string;
  topicIndex: number;
}

export function Quiz({ sessionId, topicIndex }: QuizProps) {
  const [questions, setQuestions] = useState<QuizItem[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [results, setResults] = useState<CheckResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await getQuiz(sessionId, topicIndex);
      setQuestions(res.questions);
      setAnswers(new Array(res.questions.length).fill(""));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate quiz");
    } finally {
      setLoading(false);
    }
  }

  async function handleCheck() {
    setChecking(true);
    try {
      const payload = questions.map((q, i) => ({
        question: q.question,
        correct_answer: q.answer,
        student_answer: answers[i] || "",
      }));
      const res = await checkAnswers(payload);
      setResults(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to check answers");
    } finally {
      setChecking(false);
    }
  }

  function updateAnswer(index: number, value: string) {
    setAnswers((prev) => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
        <p className="text-sm text-[var(--muted-foreground)]">
          Generating quiz questions...
        </p>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <ClipboardList className="w-12 h-12 text-[var(--muted-foreground)]" />
        <p className="text-sm text-[var(--muted-foreground)]">
          Test your knowledge with AI-generated quiz questions.
        </p>
        <button
          onClick={handleGenerate}
          className="px-5 py-2.5 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] font-medium text-sm hover:opacity-90 transition-opacity"
        >
          Generate Quiz
        </button>
        {error && (
          <p className="text-sm text-[var(--destructive)]">{error}</p>
        )}
      </div>
    );
  }

  const score = results
    ? results.filter((r) => r.correct).length
    : null;

  return (
    <div className="space-y-6">
      {score !== null && (
        <div
          className={`
            rounded-lg p-4 text-center font-semibold text-sm
            ${score === questions.length
              ? "bg-green-500/10 text-green-600"
              : score >= questions.length / 2
                ? "bg-yellow-500/10 text-yellow-600"
                : "bg-red-500/10 text-red-600"
            }
          `}
        >
          Score: {score} / {questions.length}
        </div>
      )}

      {questions.map((q, i) => {
        const result = results?.[i];
        return (
          <div
            key={i}
            className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-5"
          >
            <p className="font-medium mb-3 text-sm">
              Q{i + 1}. {q.question}
            </p>
            <input
              type="text"
              value={answers[i] || ""}
              onChange={(e) => updateAnswer(i, e.target.value)}
              placeholder="Type your answer..."
              disabled={results !== null}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ring)] disabled:opacity-60"
            />
            {result && (
              <div
                className={`mt-3 flex items-start gap-2 text-sm ${result.correct ? "text-green-600" : "text-red-500"}`}
              >
                {result.correct ? (
                  <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
                )}
                <span>{result.explanation}</span>
              </div>
            )}
          </div>
        );
      })}

      <div className="flex items-center gap-3">
        {!results ? (
          <button
            onClick={handleCheck}
            disabled={checking}
            className="px-5 py-2.5 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
          >
            {checking && <Loader2 className="w-4 h-4 animate-spin" />}
            {checking ? "Checking..." : "Submit Answers"}
          </button>
        ) : (
          <button
            onClick={() => {
              setResults(null);
              handleGenerate();
            }}
            className="flex items-center gap-1.5 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> New Quiz
          </button>
        )}
      </div>
    </div>
  );
}
