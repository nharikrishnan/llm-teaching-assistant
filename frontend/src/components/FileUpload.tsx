"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";

interface FileUploadProps {
  onUpload: (file: File) => void;
  uploading: boolean;
}

export function FileUpload({ onUpload, uploading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Please upload a PDF file.");
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        alert("File too large. Maximum size is 50 MB.");
        return;
      }
      setFileName(file.name);
      onUpload(file);
    },
    [onUpload]
  );

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      className={`
        relative rounded-xl border-2 border-dashed p-10 text-center transition-all cursor-pointer
        ${dragActive
          ? "border-[var(--primary)] bg-[var(--primary)]/5"
          : "border-[var(--border)] hover:border-[var(--primary)]/50 hover:bg-[var(--muted)]/50"
        }
      `}
    >
      <input
        type="file"
        accept=".pdf"
        onChange={handleChange}
        disabled={uploading}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-10 h-10 text-[var(--primary)] animate-spin" />
          <p className="font-medium">Processing {fileName}...</p>
          <p className="text-sm text-[var(--muted-foreground)]">
            Extracting text and identifying topics
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          {fileName ? (
            <FileText className="w-10 h-10 text-[var(--primary)]" />
          ) : (
            <Upload className="w-10 h-10 text-[var(--muted-foreground)]" />
          )}
          <p className="font-medium">
            {fileName || "Drop your PDF here or click to browse"}
          </p>
          <p className="text-sm text-[var(--muted-foreground)]">
            PDF files up to 50 MB
          </p>
        </div>
      )}
    </div>
  );
}
