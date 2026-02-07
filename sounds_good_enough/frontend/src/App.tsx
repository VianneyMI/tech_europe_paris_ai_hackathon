import { useState } from "react";
import type { CSSProperties, JSX } from "react";
import { ProcessResponse, processAudio } from "./api/client";
import ProcessingStatus from "./components/ProcessingStatus";
import Results from "./components/Results";
import UploadZone from "./components/UploadZone";

export default function App(): JSX.Element {
  const [status, setStatus] = useState<"idle" | "processing" | "done" | "error">("idle");
  const [message, setMessage] = useState<string>("Upload a track to begin.");
  const [result, setResult] = useState<ProcessResponse | null>(null);

  const handleSelectFile = async (file: File): Promise<void> => {
    setStatus("processing");
    setMessage("Separating vocals and transcribing lyrics. This may take a minute.");
    setResult(null);

    try {
      const payload = await processAudio(file);
      setResult(payload);
      setStatus("done");
      setMessage("Processing completed.");
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Unexpected error.";
      setStatus("error");
      setMessage(detail);
    }
  };

  return (
    <main style={styles.page}>
      <div style={styles.container}>
        <header>
          <h1 style={styles.title}>Sounds Good Enough</h1>
          <p style={styles.subtitle}>Upload a song to split vocals and transcribe lyrics with timestamps.</p>
        </header>
        <UploadZone disabled={status === "processing"} onSelectFile={handleSelectFile} />
        <ProcessingStatus status={status} message={message} />
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

const styles: Record<string, CSSProperties> = {
  page: {
    minHeight: "100vh",
    margin: 0,
    padding: 24,
    background: "linear-gradient(180deg, #f4f7fc 0%, #eef2f8 100%)",
    color: "#182232",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  },
  container: {
    maxWidth: 900,
    margin: "0 auto",
    display: "grid",
    gap: 16,
  },
  title: {
    margin: "0 0 8px",
    fontSize: 34,
  },
  subtitle: {
    margin: 0,
    color: "#4d596a",
  },
};
