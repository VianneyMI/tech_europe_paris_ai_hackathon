import { useRef } from "react";
import type { CSSProperties, JSX } from "react";

interface UploadZoneProps {
  disabled: boolean;
  onSelectFile: (file: File) => void;
}

const ACCEPTED_TYPES = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3"];

export default function UploadZone({ disabled, onSelectFile }: UploadZoneProps): JSX.Element {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFiles = (fileList: FileList | null): void => {
    const file = fileList?.[0];
    if (!file) {
      return;
    }
    if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(mp3|wav)$/i)) {
      window.alert("Please select an MP3 or WAV file.");
      return;
    }
    onSelectFile(file);
  };

  return (
    <section style={styles.wrapper}>
      <h2 style={styles.heading}>Upload Song</h2>
      <p style={styles.description}>Supported formats: MP3 or WAV. Maximum size: 50MB.</p>
      <input
        ref={inputRef}
        type="file"
        accept=".mp3,.wav,audio/*"
        disabled={disabled}
        style={{ display: "none" }}
        onChange={(event) => handleFiles(event.target.files)}
      />
      <button
        type="button"
        disabled={disabled}
        style={disabled ? styles.buttonDisabled : styles.button}
        onClick={() => inputRef.current?.click()}
      >
        Choose Audio File
      </button>
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
    margin: "0 0 8px",
    fontSize: 20,
  },
  description: {
    margin: "0 0 16px",
    color: "#4d596a",
  },
  button: {
    backgroundColor: "#1041d1",
    color: "#fff",
    border: 0,
    borderRadius: 8,
    padding: "10px 16px",
    cursor: "pointer",
    fontWeight: 600,
  },
  buttonDisabled: {
    backgroundColor: "#98a8ce",
    color: "#fff",
    border: 0,
    borderRadius: 8,
    padding: "10px 16px",
    cursor: "not-allowed",
    fontWeight: 600,
  },
};
