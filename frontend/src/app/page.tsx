"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileUpload } from "@/components/FileUpload";
import { uploadPdf } from "@/lib/api";
import { BookOpen, Video, Search, MessageCircle } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setUploading(true);
    setError(null);
    try {
      const data = await uploadPdf(file);
      sessionStorage.setItem("ta_session", JSON.stringify(data));
      router.push(`/course?session=${data.session_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  const features = [
    {
      icon: BookOpen,
      title: "Interactive Lessons",
      desc: "AI breaks your document into topics and explains each one clearly.",
    },
    {
      icon: Video,
      title: "Video Lessons",
      desc: "Auto-generated narrated slide videos for every topic.",
    },
    {
      icon: MessageCircle,
      title: "Ask Questions",
      desc: "Chat with an AI teacher about any topic in your document.",
    },
    {
      icon: Search,
      title: "Industry Standards",
      desc: "Discover current best practices via real-time web search.",
    },
  ];

  return (
    <main className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--border)] px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <BookOpen className="w-7 h-7 text-[var(--primary)]" />
          <h1 className="text-xl font-bold">Teaching Assistant</h1>
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="max-w-2xl w-full text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 tracking-tight">
            Learn anything from your PDFs
          </h2>
          <p className="text-lg text-[var(--muted-foreground)]">
            Upload a PDF document and get AI-powered lessons, quizzes,
            narrated videos, and real-time industry insights.
          </p>
        </div>

        <div className="max-w-lg w-full mb-16">
          <FileUpload onUpload={handleUpload} uploading={uploading} />
          {error && (
            <p className="mt-4 text-sm text-[var(--destructive)] text-center">
              {error}
            </p>
          )}
        </div>

        <div className="max-w-4xl w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 text-center"
            >
              <f.icon className="w-10 h-10 mx-auto mb-4 text-[var(--primary)]" />
              <h3 className="font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-[var(--muted-foreground)]">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
