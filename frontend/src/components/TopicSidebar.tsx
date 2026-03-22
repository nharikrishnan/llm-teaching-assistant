"use client";

import { BookOpen, CheckCircle2 } from "lucide-react";
import type { Topic } from "@/types";

interface TopicSidebarProps {
  topics: Topic[];
  currentIndex: number;
  completedTopics: Set<number>;
  onSelect: (index: number) => void;
}

export function TopicSidebar({
  topics,
  currentIndex,
  completedTopics,
  onSelect,
}: TopicSidebarProps) {
  return (
    <aside className="w-72 shrink-0 border-r border-[var(--border)] bg-[var(--card)] flex flex-col h-full">
      <div className="p-4 border-b border-[var(--border)] flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-[var(--primary)]" />
        <h2 className="font-semibold text-sm">Course Outline</h2>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        {topics.map((topic, i) => {
          const isActive = i === currentIndex;
          const isDone = completedTopics.has(i);
          return (
            <button
              key={i}
              onClick={() => onSelect(i)}
              className={`
                w-full text-left px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors flex items-start gap-2
                ${isActive
                  ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                  : "hover:bg-[var(--muted)] text-[var(--foreground)]"
                }
              `}
            >
              <span className="shrink-0 mt-0.5">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <span
                    className={`
                      inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold border
                      ${isActive ? "border-[var(--primary-foreground)]" : "border-current"}
                    `}
                  >
                    {i + 1}
                  </span>
                )}
              </span>
              <span className="leading-tight">{topic.title}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
