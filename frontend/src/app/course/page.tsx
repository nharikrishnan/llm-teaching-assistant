"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  BookOpen,
  GraduationCap,
  MessageCircle,
  Globe,
  Video,
  ChevronLeft,
  ChevronRight,
  Home,
} from "lucide-react";
import type { Topic } from "@/types";
import { TopicSidebar } from "@/components/TopicSidebar";
import { VideoPlayer } from "@/components/VideoPlayer";
import { TeachingContent } from "@/components/TeachingContent";
import { Quiz } from "@/components/Quiz";
import { ChatPanel } from "@/components/ChatPanel";
import { IndustrySearch } from "@/components/IndustrySearch";

type TabId = "lesson" | "quiz" | "chat" | "standards";

const tabs: { id: TabId; label: string; icon: typeof BookOpen }[] = [
  { id: "lesson", label: "Lesson", icon: BookOpen },
  { id: "quiz", label: "Quiz", icon: GraduationCap },
  { id: "chat", label: "Chat", icon: MessageCircle },
  { id: "standards", label: "Industry Standards", icon: Globe },
];

function CourseContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get("session") || "";

  const [topics, setTopics] = useState<Topic[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<TabId>("lesson");
  const [completedTopics, setCompletedTopics] = useState<Set<number>>(
    new Set()
  );
  const [showVideo, setShowVideo] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("ta_session");
    if (raw) {
      try {
        const data = JSON.parse(raw);
        if (data.topics) setTopics(data.topics);
      } catch {
        /* ignore */
      }
    }
  }, []);

  useEffect(() => {
    setActiveTab("lesson");
    setShowVideo(false);
    setCompletedTopics((prev) => {
      const next = new Set(prev);
      next.add(currentIndex);
      return next;
    });
  }, [currentIndex]);

  if (!sessionId || topics.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-[var(--muted-foreground)]">
            No active session. Please upload a document first.
          </p>
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] text-sm"
          >
            Go to Upload
          </button>
        </div>
      </div>
    );
  }

  const current = topics[currentIndex];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top header */}
      <header className="border-b border-[var(--border)] px-4 py-3 flex items-center gap-3 shrink-0">
        <button
          onClick={() => router.push("/")}
          className="p-1.5 rounded-lg hover:bg-[var(--muted)] transition-colors"
          title="Back to home"
        >
          <Home className="w-5 h-5 text-[var(--muted-foreground)]" />
        </button>
        <div className="h-5 w-px bg-[var(--border)]" />
        <BookOpen className="w-5 h-5 text-[var(--primary)]" />
        <h1 className="font-semibold text-sm">Teaching Assistant</h1>
        <span className="text-xs text-[var(--muted-foreground)] ml-2">
          Topic {currentIndex + 1} of {topics.length}
        </span>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <TopicSidebar
          topics={topics}
          currentIndex={currentIndex}
          completedTopics={completedTopics}
          onSelect={setCurrentIndex}
        />

        {/* Content area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Topic header */}
          <div className="px-8 pt-6 pb-4 border-b border-[var(--border)] shrink-0">
            <h2 className="text-2xl font-bold mb-1">{current.title}</h2>
            <p className="text-sm text-[var(--muted-foreground)]">
              Topic {currentIndex + 1} of {topics.length}
            </p>
          </div>

          {/* Video section (toggleable) */}
          <div className="px-8 pt-4 shrink-0">
            {!showVideo ? (
              <button
                onClick={() => setShowVideo(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[var(--muted)] transition-colors"
              >
                <Video className="w-4 h-4 text-[var(--primary)]" />
                Show Video Lesson
              </button>
            ) : (
              <div className="max-w-2xl">
                <VideoPlayer
                  sessionId={sessionId}
                  topicIndex={currentIndex}
                />
                <button
                  onClick={() => setShowVideo(false)}
                  className="mt-2 text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                >
                  Hide video
                </button>
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="px-8 pt-4 border-b border-[var(--border)] flex gap-1 shrink-0">
            {tabs.map((tab) => {
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-colors
                    ${active
                      ? "border-[var(--primary)] text-[var(--primary)]"
                      : "border-transparent text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                    }
                  `}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto px-8 py-6">
            {activeTab === "lesson" && (
              <TeachingContent
                key={currentIndex}
                sessionId={sessionId}
                topicIndex={currentIndex}
                topicTitle={current.title}
              />
            )}
            {activeTab === "quiz" && (
              <Quiz
                key={currentIndex}
                sessionId={sessionId}
                topicIndex={currentIndex}
              />
            )}
            {activeTab === "chat" && (
              <ChatPanel
                key={currentIndex}
                sessionId={sessionId}
                topicIndex={currentIndex}
                topicTitle={current.title}
              />
            )}
            {activeTab === "standards" && (
              <IndustrySearch
                key={currentIndex}
                topicTitle={current.title}
                topicContent={current.content}
              />
            )}
          </div>

          {/* Navigation footer */}
          <div className="px-8 py-4 border-t border-[var(--border)] flex justify-between items-center shrink-0">
            <button
              onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
              disabled={currentIndex === 0}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[var(--muted)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>
            <button
              onClick={() =>
                setCurrentIndex((i) => Math.min(topics.length - 1, i + 1))
              }
              disabled={currentIndex === topics.length - 1}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] text-sm hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}

export default function CoursePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <p className="text-[var(--muted-foreground)]">Loading...</p>
        </div>
      }
    >
      <CourseContent />
    </Suspense>
  );
}
