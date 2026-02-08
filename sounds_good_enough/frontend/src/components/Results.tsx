import type { CSSProperties, JSX } from "react";

import type { LyricsTimestamp } from "../api/client";
import { toAbsoluteAudioUrl } from "../api/client";
import KaraokePlayer from "./KaraokePlayer";

interface ResultsProps {
  lyrics: string;
  timestamps: LyricsTimestamp[];
  vocalsUrl: string;
  instrumentalUrl: string;
}

export default function Results({ lyrics, timestamps, vocalsUrl, instrumentalUrl }: ResultsProps): JSX.Element {
  return (
    <section style={styles.wrapper}>
      {/* ── Karaoke player is the hero ── */}
      <KaraokePlayer instrumentalUrl={instrumentalUrl} timestamps={timestamps} />

      {/* ── Vocals & Instrumental ── */}
      <div style={styles.playerRow}>
        <div style={styles.playerBlock}>
          <h3 style={styles.subheading}>Vocals</h3>
          <audio controls src={toAbsoluteAudioUrl(vocalsUrl)} style={styles.audio} />
          <a
            href={toAbsoluteAudioUrl(vocalsUrl)}
            download
            style={styles.downloadBtn}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download vocals.wav
          </a>
        </div>
        <div style={styles.playerBlock}>
          <h3 style={styles.subheading}>Instrumental</h3>
          <audio controls src={toAbsoluteAudioUrl(instrumentalUrl)} style={styles.audio} />
          <a
            href={toAbsoluteAudioUrl(instrumentalUrl)}
            download
            style={styles.downloadBtn}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download instrumental.wav
          </a>
        </div>
      </div>

      {/* ── Raw data (collapsible) ── */}
      <details style={styles.details}>
        <summary style={styles.summary}>Raw Lyrics</summary>
        <pre style={styles.lyrics}>{lyrics || "(No transcription text returned)"}</pre>
      </details>

      <details style={styles.details}>
        <summary style={styles.summary}>Raw Timestamps</summary>
        {timestamps.length === 0 ? (
          <p style={styles.empty}>No timestamp segments returned.</p>
        ) : (
          <ul style={styles.list}>
            {timestamps.map((item, idx) => (
              <li key={`${item.start_s}-${item.stop_s}-${idx}`} style={styles.listItem}>
                [{item.start_s.toFixed(2)}s - {item.stop_s.toFixed(2)}s] {item.text}
              </li>
            ))}
          </ul>
        )}
      </details>
    </section>
  );
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    display: "grid",
    gap: 16,
  },
  subheading: {
    margin: "0 0 8px",
    fontSize: 16,
    fontWeight: 600,
    color: "#e8e0f0",
  },
  playerRow: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: 16,
  },
  playerBlock: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
    background: "rgba(255, 255, 255, 0.05)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    border: "1px solid rgba(255, 255, 255, 0.08)",
    borderRadius: 14,
    padding: 18,
  },
  audio: {
    width: "100%",
    borderRadius: 8,
  },
  downloadBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    color: "#c08fff",
    fontSize: 13,
    fontWeight: 500,
    textDecoration: "none",
    padding: "6px 0",
    transition: "color 150ms ease",
  },
  lyrics: {
    whiteSpace: "pre-wrap",
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    borderRadius: 10,
    padding: 14,
    border: "1px solid rgba(255, 255, 255, 0.06)",
    color: "rgba(232, 224, 240, 0.7)",
    fontSize: 13,
    lineHeight: 1.7,
    margin: "10px 0 0",
  },
  empty: {
    margin: 0,
    color: "rgba(232, 224, 240, 0.5)",
    fontSize: 14,
  },
  details: {
    background: "rgba(255, 255, 255, 0.04)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    border: "1px solid rgba(255, 255, 255, 0.08)",
    borderRadius: 14,
    padding: "12px 18px",
  },
  summary: {
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 14,
    color: "rgba(232, 224, 240, 0.7)",
    marginBottom: 6,
  },
  list: {
    margin: "10px 0 0",
    padding: "0 0 0 20px",
    color: "rgba(232, 224, 240, 0.6)",
    fontSize: 13,
    lineHeight: 1.7,
  },
  listItem: {
    marginBottom: 2,
  },
};
