"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Loader2, RefreshCw, Sparkles } from "lucide-react";
import { getExplanation } from "@/lib/api";

interface TeachingContentProps {
  sessionId: string;
  topicIndex: number;
  topicTitle: string;
}

export function TeachingContent({
  sessionId,
  topicIndex,
  topicTitle,
}: TeachingContentProps) {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await getExplanation(sessionId, topicIndex);
      setExplanation(res.explanation);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate explanation");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
        <p className="text-sm text-[var(--muted-foreground)]">
          Generating explanation for &quot;{topicTitle}&quot;...
        </p>
      </div>
    );
  }

  if (!explanation) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <Sparkles className="w-12 h-12 text-[var(--muted-foreground)]" />
        <p className="text-sm text-[var(--muted-foreground)]">
          Click below to generate an AI-powered explanation of this topic.
        </p>
        <button
          onClick={handleGenerate}
          className="px-5 py-2.5 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] font-medium text-sm hover:opacity-90 transition-opacity"
        >
          Generate Explanation
        </button>
        {error && (
          <p className="text-sm text-[var(--destructive)]">{error}</p>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="prose max-w-none">
        <ReactMarkdown>{explanation}</ReactMarkdown>
      </div>
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleGenerate}
          className="flex items-center gap-1.5 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Regenerate
        </button>
      </div>
    </div>
  );
}
