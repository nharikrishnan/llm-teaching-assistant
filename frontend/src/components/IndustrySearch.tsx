"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Search, Loader2, ExternalLink, Globe } from "lucide-react";
import { searchIndustryStandards } from "@/lib/api";
import type { SourceLink } from "@/types";

interface IndustrySearchProps {
  topicTitle: string;
  topicContent: string;
}

export function IndustrySearch({ topicTitle, topicContent }: IndustrySearchProps) {
  const [summary, setSummary] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceLink[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch() {
    setLoading(true);
    setError(null);
    try {
      const res = await searchIndustryStandards(topicTitle, topicContent);
      setSummary(res.summary);
      setSources(res.sources);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2 className="w-8 h-8 text-[var(--primary)] animate-spin" />
        <p className="text-sm text-[var(--muted-foreground)]">
          Searching the web for industry standards...
        </p>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <Globe className="w-12 h-12 text-[var(--muted-foreground)]" />
        <p className="text-sm text-[var(--muted-foreground)] text-center max-w-md">
          Search the web for current industry standards and best practices
          related to &quot;{topicTitle}&quot;.
        </p>
        <button
          onClick={handleSearch}
          className="px-5 py-2.5 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] font-medium text-sm hover:opacity-90 transition-opacity flex items-center gap-2"
        >
          <Search className="w-4 h-4" /> Search Industry Standards
        </button>
        {error && (
          <p className="text-sm text-[var(--destructive)]">{error}</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="prose max-w-none">
        <ReactMarkdown>{summary}</ReactMarkdown>
      </div>

      {sources.length > 0 && (
        <div>
          <h3 className="font-semibold text-sm mb-3 text-[var(--muted-foreground)]">
            Sources
          </h3>
          <div className="space-y-2">
            {sources.map((s, i) => (
              <a
                key={i}
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--muted)] transition-colors"
              >
                <ExternalLink className="w-4 h-4 mt-0.5 shrink-0 text-[var(--primary)]" />
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{s.title}</p>
                  {s.snippet && (
                    <p className="text-xs text-[var(--muted-foreground)] mt-0.5 line-clamp-2">
                      {s.snippet}
                    </p>
                  )}
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleSearch}
          className="flex items-center gap-1.5 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
        >
          <Search className="w-3.5 h-3.5" /> Search Again
        </button>
      </div>
    </div>
  );
}
