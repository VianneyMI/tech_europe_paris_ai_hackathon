import type { CSSProperties, JSX } from "react";

interface ProcessingStatusProps {
  status: "idle" | "processing" | "done" | "error";
  message: string;
}

export default function ProcessingStatus({ status, message }: ProcessingStatusProps): JSX.Element {
  const color =
    status === "processing"
      ? "#946100"
      : status === "done"
        ? "#096b2f"
        : status === "error"
          ? "#8b1212"
          : "#4d596a";

  return (
    <section style={{ ...styles.wrapper, borderColor: color }}>
      <h2 style={styles.heading}>Status</h2>
      <p style={{ margin: 0, color }}>{message}</p>
    </section>
  );
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    border: "1px solid #d3d7df",
    borderRadius: 10,
    padding: 16,
    backgroundColor: "#ffffff",
  },
  heading: {
    margin: "0 0 8px",
    fontSize: 18,
  },
};
