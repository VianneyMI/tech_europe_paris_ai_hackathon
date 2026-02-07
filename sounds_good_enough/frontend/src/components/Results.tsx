import type { CSSProperties, JSX } from "react";

import { LyricsTimestamp, toAbsoluteAudioUrl } from "../api/client";

interface ResultsProps {
  lyrics: string;
  timestamps: LyricsTimestamp[];
  vocalsUrl: string;
  instrumentalUrl: string;
}

export default function Results({ lyrics, timestamps, vocalsUrl, instrumentalUrl }: ResultsProps): JSX.Element {
  return (
    <section style={styles.wrapper}>
      <h2 style={styles.heading}>Results</h2>

      <div style={styles.playerRow}>
        <div style={styles.playerBlock}>
          <h3 style={styles.subheading}>Vocals</h3>
          <audio controls src={toAbsoluteAudioUrl(vocalsUrl)} style={styles.audio} />
          <a href={toAbsoluteAudioUrl(vocalsUrl)} download>
            Download vocals.wav
          </a>
        </div>
        <div style={styles.playerBlock}>
          <h3 style={styles.subheading}>Instrumental</h3>
          <audio controls src={toAbsoluteAudioUrl(instrumentalUrl)} style={styles.audio} />
          <a href={toAbsoluteAudioUrl(instrumentalUrl)} download>
            Download instrumental.wav
          </a>
        </div>
      </div>

      <div>
        <h3 style={styles.subheading}>Lyrics</h3>
        <pre style={styles.lyrics}>{lyrics || "(No transcription text returned)"}</pre>
      </div>

      <div>
        <h3 style={styles.subheading}>Timestamps</h3>
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
      </div>
    </section>
  );
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    border: "1px solid #d3d7df",
    borderRadius: 10,
    padding: 20,
    backgroundColor: "#ffffff",
  },
  heading: {
    margin: "0 0 16px",
    fontSize: 20,
  },
  subheading: {
    margin: "0 0 8px",
    fontSize: 17,
  },
  playerRow: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: 16,
    marginBottom: 20,
  },
  playerBlock: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  audio: {
    width: "100%",
  },
  lyrics: {
    whiteSpace: "pre-wrap",
    backgroundColor: "#f6f8fc",
    borderRadius: 8,
    padding: 12,
    border: "1px solid #e2e7f1",
  },
  empty: {
    margin: 0,
    color: "#4d596a",
  },
  list: {
    margin: 0,
    padding: "0 0 0 20px",
  },
  listItem: {
    marginBottom: 4,
  },
};
