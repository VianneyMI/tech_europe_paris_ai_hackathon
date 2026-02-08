import { useRef, useState } from "react";
import type { DragEvent } from "react";
import type { CSSProperties, JSX } from "react";

interface UploadZoneProps {
  disabled: boolean;
  onSelectFile: (file: File) => void;
}

const ACCEPTED_TYPES = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3"];
const MAX_BYTES = 50 * 1024 * 1024;

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadZone({ disabled, onSelectFile }: UploadZoneProps): JSX.Element {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  const handleFiles = (fileList: FileList | null): void => {
    const file = fileList?.[0];
    if (!file) {
      return;
    }
    if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(mp3|wav)$/i)) {
      window.alert("Please select an MP3 or WAV file.");
      return;
    }
    if (file.size > MAX_BYTES) {
      window.alert("File exceeds maximum size of 50MB.");
      return;
    }
    setSelectedFile(file);
  };

  const handleDragOver = (event: DragEvent<HTMLElement>): void => {
    event.preventDefault();
    if (disabled) {
      return;
    }
    setIsDragOver(true);
  };

  const handleDragEnter = (event: DragEvent<HTMLElement>): void => {
    event.preventDefault();
    if (disabled) {
      return;
    }
    setIsDragOver(true);
  };

  const handleDragLeave = (event: DragEvent<HTMLElement>): void => {
    event.preventDefault();
    if (disabled) {
      return;
    }
    const nextTarget = event.relatedTarget;
    if (nextTarget instanceof Node && event.currentTarget.contains(nextTarget)) {
      return;
    }
    setIsDragOver(false);
  };

  const handleDrop = (event: DragEvent<HTMLElement>): void => {
    event.preventDefault();
    if (disabled) {
      return;
    }
    setIsDragOver(false);
    handleFiles(event.dataTransfer.files);
  };

  const handleProcessClick = (): void => {
    if (!selectedFile || disabled) {
      return;
    }
    setSelectedFile(null);
    onSelectFile(selectedFile);
  };

  return (
    <section
      style={{
        ...styles.wrapper,
        ...(isDragOver && !disabled ? styles.wrapperDragOver : null),
      }}
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
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
      {selectedFile ? (
        <p style={styles.fileInfo}>
          {selectedFile.name} - {formatFileSize(selectedFile.size)}
        </p>
      ) : null}
      <button
        type="button"
        disabled={disabled || selectedFile === null}
        style={disabled || selectedFile === null ? styles.processButtonDisabled : styles.processButton}
        onClick={handleProcessClick}
      >
        Process Song
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
    transition: "border-color 120ms ease, background-color 120ms ease",
  },
  wrapperDragOver: {
    borderColor: "#3f6ce5",
    backgroundColor: "#f3f7ff",
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
    marginRight: 8,
  },
  buttonDisabled: {
    backgroundColor: "#98a8ce",
    color: "#fff",
    border: 0,
    borderRadius: 8,
    padding: "10px 16px",
    cursor: "not-allowed",
    fontWeight: 600,
    marginRight: 8,
  },
  processButton: {
    backgroundColor: "#0d7f5f",
    color: "#fff",
    border: 0,
    borderRadius: 8,
    padding: "10px 16px",
    cursor: "pointer",
    fontWeight: 600,
  },
  processButtonDisabled: {
    backgroundColor: "#9ec8bc",
    color: "#fff",
    border: 0,
    borderRadius: 8,
    padding: "10px 16px",
    cursor: "not-allowed",
    fontWeight: 600,
  },
  fileInfo: {
    margin: "14px 0 10px",
    color: "#2f3b52",
    fontWeight: 600,
  },
};
