import type { JSX } from "react";
import "./ProcessingStatus.css";

interface ProcessingStatusProps {
  status: "idle" | "processing" | "done" | "error";
  message: string;
}

export default function ProcessingStatus({ status, message }: ProcessingStatusProps): JSX.Element {
  const isError = status === "error";

  return (
    <section className="glass-card processing-status-card">
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        {status === "processing" ? (
          <div className="processing-equalizer" aria-hidden="true">
            <div className="processing-equalizer-bar" />
            <div className="processing-equalizer-bar" />
            <div className="processing-equalizer-bar" />
            <div className="processing-equalizer-bar" />
            <div className="processing-equalizer-bar" />
          </div>
        ) : null}
        <p
          style={{
            margin: 0,
            fontSize: 15,
            fontWeight: 500,
            color: isError ? "#ff6b6b" : "rgba(232, 224, 240, 0.8)",
          }}
        >
          {message}
        </p>
      </div>
    </section>
  );
}
