import { useRef, useState } from "react";
import type { JSX } from "react";
import type { ProcessResponse } from "./api/client";
import { fetchDemo, fetchProcessJob, processAudio, processAudioFromUrl } from "./api/client";
import ProcessingStatus from "./components/ProcessingStatus";
import Results from "./components/Results";
import UploadZone from "./components/UploadZone";
import "./App.css";

const JOB_POLL_MS = 2000;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export default function App(): JSX.Element {
  const [status, setStatus] = useState<"idle" | "processing" | "done" | "error">("idle");
  const [message, setMessage] = useState<string>("Upload a track to begin.");
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const requestVersionRef = useRef<number>(0);

  const resetToIdle = (): void => {
    requestVersionRef.current += 1;
    setStatus("idle");
    setMessage("Upload a track to begin.");
    setResult(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSelectFile = async (file: File): Promise<void> => {
    const version = requestVersionRef.current + 1;
    requestVersionRef.current = version;
    setStatus("processing");
    setMessage(`Processing ${file.name}. This may take a minute.`);
    setResult(null);

    try {
      const payload = await processAudio(file);
      if (requestVersionRef.current !== version) {
        return;
      }
      setResult(payload);
      setStatus("done");
      setMessage("Processing completed.");
    } catch (error) {
      if (requestVersionRef.current !== version) {
        return;
      }
      const detail = error instanceof Error ? error.message : "Unexpected error.";
      setStatus("error");
      setMessage(detail);
    }
  };

  const handleSubmitUrl = async (url: string): Promise<void> => {
    const version = requestVersionRef.current + 1;
    requestVersionRef.current = version;
    setStatus("processing");
    setMessage("Queued YouTube link. Starting background processing...");
    setResult(null);

    try {
      const initialJob = await processAudioFromUrl(url);
      if (requestVersionRef.current !== version) {
        return;
      }
      let currentJob = initialJob;
      while (currentJob.status === "queued" || currentJob.status === "processing") {
        setMessage(
          currentJob.status === "queued"
            ? "Queued. Waiting for worker..."
            : "Processing YouTube audio in background...",
        );
        await delay(JOB_POLL_MS);
        if (requestVersionRef.current !== version) {
          return;
        }
        currentJob = await fetchProcessJob(currentJob.job_id);
      }

      if (currentJob.status === "error") {
        throw new Error(currentJob.error ?? "Background processing failed.");
      }
      if (!currentJob.result) {
        throw new Error("Background processing finished without a result payload.");
      }
      setResult(currentJob.result);
      setStatus("done");
      setMessage("YouTube processing completed.");
    } catch (error) {
      if (requestVersionRef.current !== version) {
        return;
      }
      const detail = error instanceof Error ? error.message : "Unexpected error.";
      setStatus("error");
      setMessage(detail);
    }
  };

  const handleTryDemo = async (): Promise<void> => {
    const version = requestVersionRef.current + 1;
    requestVersionRef.current = version;
    setStatus("processing");
    setMessage("Loading demo song...");
    setResult(null);

    try {
      const payload = await fetchDemo();
      if (requestVersionRef.current !== version) {
        return;
      }
      setResult(payload);
      setStatus("done");
      setMessage("Demo loaded.");
    } catch (error) {
      if (requestVersionRef.current !== version) {
        return;
      }
      const detail = error instanceof Error ? error.message : "Unexpected error.";
      setStatus("error");
      setMessage(detail);
    }
  };

  return (
    <main className="app-page">
      <div className="app-container">
        <header className="app-header">
          <div>
            <h1 className="app-title">KaraAI</h1>
            <p className="app-subtitle">Drop a song. Get karaoke.</p>
          </div>
          {status === "done" ? (
            <button type="button" className="btn-secondary" onClick={resetToIdle}>
              New Song
            </button>
          ) : null}
        </header>

        {status !== "done" ? (
          <UploadZone
            disabled={status === "processing"}
            onSelectFile={handleSelectFile}
            onSubmitUrl={handleSubmitUrl}
          />
        ) : null}

        {status === "idle" ? (
          <button type="button" className="btn-secondary" onClick={handleTryDemo}>
            Try with a demo song
          </button>
        ) : null}

        {(status === "processing" || status === "error") ? (
          <ProcessingStatus status={status} message={message} />
        ) : null}

        {status === "error" ? (
          <button type="button" className="btn-secondary" onClick={resetToIdle}>
            Try Again
          </button>
        ) : null}

        {result ? (
          <Results
            lyrics={result.lyrics}
            timestamps={result.lyrics_with_timestamps}
            vocalsUrl={result.vocals_url}
            instrumentalUrl={result.instrumental_url}
          />
        ) : null}
      </div>
    </main>
  );
}
