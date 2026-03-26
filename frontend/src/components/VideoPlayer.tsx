"use client";

import { useState, useEffect, useRef } from "react";
import { Video, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { generateVideo, getVideoStatus } from "@/lib/api";

interface VideoPlayerProps {
  sessionId: string;
  topicIndex: number;
}

export function VideoPlayer({ sessionId, topicIndex }: VideoPlayerProps) {
  const [, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  useEffect(() => {
    setJobId(null);
    setStatus("idle");
    setVideoUrl(null);
    setError(null);
    if (pollingRef.current) clearInterval(pollingRef.current);
  }, [topicIndex]);

  async function handleGenerate() {
    setError(null);
    setStatus("starting");
    try {
      const res = await generateVideo(sessionId, topicIndex);
      setJobId(res.job_id);

      if (res.status === "completed") {
        setStatus("completed");
        const statusRes = await getVideoStatus(res.job_id);
        if (statusRes.video_url) setVideoUrl(statusRes.video_url);
        return;
      }

      setStatus("processing");
      pollingRef.current = setInterval(async () => {
        try {
          const s = await getVideoStatus(res.job_id);
          if (s.status === "completed" && s.video_url) {
            setStatus("completed");
            setVideoUrl(s.video_url);
            if (pollingRef.current) clearInterval(pollingRef.current);
          } else if (s.status === "failed") {
            setStatus("failed");
            setError(s.error || "Video generation failed.");
            if (pollingRef.current) clearInterval(pollingRef.current);
          }
        } catch {
          /* keep polling */
        }
      }, 3000);
    } catch (e) {
      setStatus("failed");
      setError(e instanceof Error ? e.message : "Failed to start video generation");
    }
  }

  if (videoUrl) {
    return (
      <div className="rounded-xl overflow-hidden border border-[var(--border)] bg-black">
        <video
          src={videoUrl}
          controls
          className="w-full aspect-video"
          autoPlay
        />
        <div className="p-2 flex justify-end bg-[var(--card)]">
          <button
            onClick={() => {
              setVideoUrl(null);
              setStatus("idle");
              setJobId(null);
            }}
            className="text-xs flex items-center gap-1 text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
          >
            <RefreshCw className="w-3 h-3" /> Regenerate
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/30 p-8 text-center">
      {status === "idle" && (
        <>
          <Video className="w-12 h-12 mx-auto mb-4 text-[var(--muted-foreground)]" />
          <p className="text-sm text-[var(--muted-foreground)] mb-4">
            Generate a narrated video lesson for this topic
          </p>
          <button
            onClick={handleGenerate}
            className="px-5 py-2.5 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] font-medium text-sm hover:opacity-90 transition-opacity"
          >
            Generate Video
          </button>
        </>
      )}

      {(status === "starting" || status === "processing") && (
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-10 h-10 text-[var(--primary)] animate-spin" />
          <p className="font-medium text-sm">Generating video lesson...</p>
          <p className="text-xs text-[var(--muted-foreground)]">
            Creating slides, narration, and assembling video. This may take a minute.
          </p>
        </div>
      )}

      {status === "failed" && (
        <div className="flex flex-col items-center gap-3">
          <AlertCircle className="w-10 h-10 text-[var(--destructive)]" />
          <p className="text-sm text-[var(--destructive)]">{error}</p>
          <button
            onClick={handleGenerate}
            className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[var(--muted)]"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
