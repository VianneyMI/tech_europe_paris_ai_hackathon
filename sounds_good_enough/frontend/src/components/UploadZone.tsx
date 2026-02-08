import { useRef, useState } from "react";
import type { DragEvent } from "react";
import type { CSSProperties, JSX } from "react";

interface UploadZoneProps {
  disabled: boolean;
  onSelectFile: (file: File) => void;
  onSubmitUrl: (url: string) => void;
}

const ACCEPTED_TYPES = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3"];
const MAX_BYTES = 50 * 1024 * 1024;

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadZone({ disabled, onSelectFile, onSubmitUrl }: UploadZoneProps): JSX.Element {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [urlInput, setUrlInput] = useState<string>("");
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

  const handleStartKaraoke = (): void => {
    if (!selectedFile || disabled) {
      return;
    }
    const file = selectedFile;
    setSelectedFile(null);
    onSelectFile(file);
  };

  const handleProcessUrlClick = (): void => {
    const url = urlInput.trim();
    if (!url || disabled) {
      return;
    }
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      window.alert("Please paste a valid URL starting with http:// or https://.");
      return;
    }
    setUrlInput("");
    onSubmitUrl(url);
  };

  return (
    <section className="glass-card">
      {/* ── File Drop Zone ── */}
      <input
        ref={inputRef}
        type="file"
        accept=".mp3,.wav,audio/*"
        disabled={disabled}
        style={{ display: "none" }}
        onChange={(event) => handleFiles(event.target.files)}
      />

      <div
        role="button"
        tabIndex={0}
        style={{
          ...styles.dropZone,
          ...(isDragOver && !disabled ? styles.dropZoneDragOver : null),
          ...(disabled ? styles.dropZoneDisabled : null),
          ...(selectedFile ? styles.dropZoneWithFile : null),
        }}
        onClick={() => {
          if (!disabled && !selectedFile) {
            inputRef.current?.click();
          }
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            if (!disabled && !selectedFile) {
              inputRef.current?.click();
            }
          }
        }}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <div style={styles.fileSelectedContent}>
            <div style={styles.fileIcon}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
            </div>
            <div style={styles.fileDetails}>
              <span style={styles.fileName}>{selectedFile.name}</span>
              <span style={styles.fileSize}>{formatFileSize(selectedFile.size)}</span>
            </div>
            <div style={styles.fileActions}>
              <button
                type="button"
                className="btn-primary"
                disabled={disabled}
                onClick={(event) => {
                  event.stopPropagation();
                  handleStartKaraoke();
                }}
              >
                Start Karaoke!
              </button>
              <button
                type="button"
                style={styles.changeFileLink}
                disabled={disabled}
                onClick={(event) => {
                  event.stopPropagation();
                  setSelectedFile(null);
                  inputRef.current?.click();
                }}
              >
                Change file
              </button>
            </div>
          </div>
        ) : (
          <div style={styles.dropZoneContent}>
            <div style={styles.musicIcon}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
            </div>
            <p style={styles.dropZoneTitle}>Drop your track here</p>
            <p style={styles.dropZoneSub}>or click to browse &middot; MP3 / WAV &middot; up to 50MB</p>
          </div>
        )}
      </div>

      {/* ── Divider ── */}
      <div style={styles.divider}>
        <div style={styles.dividerLine} />
        <span style={styles.dividerText}>or paste a YouTube link</span>
        <div style={styles.dividerLine} />
      </div>

      {/* ── YouTube URL Input ── */}
      <div style={styles.urlRow}>
        <input
          type="url"
          value={urlInput}
          disabled={disabled}
          onChange={(event) => setUrlInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              handleProcessUrlClick();
            }
          }}
          placeholder="https://www.youtube.com/watch?v=..."
          style={styles.urlInput}
        />
        <button
          type="button"
          className="btn-primary"
          disabled={disabled || urlInput.trim().length === 0}
          onClick={handleProcessUrlClick}
        >
          Go!
        </button>
      </div>
    </section>
  );
}

const styles: Record<string, CSSProperties> = {
  /* ── Drop zone ── */
  dropZone: {
    border: "2px dashed rgba(200, 64, 255, 0.3)",
    borderRadius: 14,
    padding: 32,
    cursor: "pointer",
    transition: "border-color 200ms ease, background 200ms ease, box-shadow 200ms ease",
    background: "rgba(200, 64, 255, 0.03)",
    textAlign: "center",
  },
  dropZoneDragOver: {
    borderColor: "#ff2d78",
    background: "rgba(255, 45, 120, 0.06)",
    boxShadow: "0 0 30px rgba(255, 45, 120, 0.12) inset",
  },
  dropZoneDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  dropZoneWithFile: {
    borderStyle: "solid",
    borderColor: "rgba(200, 64, 255, 0.4)",
    background: "rgba(200, 64, 255, 0.06)",
    cursor: "default",
  },
  dropZoneContent: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
  },
  musicIcon: {
    color: "rgba(200, 64, 255, 0.6)",
    marginBottom: 4,
  },
  dropZoneTitle: {
    margin: 0,
    fontSize: 18,
    fontWeight: 600,
    color: "#e8e0f0",
  },
  dropZoneSub: {
    margin: 0,
    fontSize: 13,
    color: "rgba(232, 224, 240, 0.5)",
  },

  /* ── File selected state ── */
  fileSelectedContent: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    flexWrap: "wrap",
    justifyContent: "center",
    textAlign: "left",
  },
  fileIcon: {
    color: "#c840ff",
    flexShrink: 0,
  },
  fileDetails: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
    flex: 1,
    minWidth: 140,
  },
  fileName: {
    fontSize: 15,
    fontWeight: 600,
    color: "#e8e0f0",
    wordBreak: "break-all",
  },
  fileSize: {
    fontSize: 13,
    color: "rgba(232, 224, 240, 0.5)",
  },
  fileActions: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 6,
    flexShrink: 0,
  },
  changeFileLink: {
    background: "none",
    border: "none",
    color: "rgba(200, 143, 255, 0.7)",
    fontSize: 12,
    cursor: "pointer",
    padding: 0,
    fontFamily: "'Outfit', sans-serif",
    transition: "color 150ms ease",
  },

  /* ── Divider ── */
  divider: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    margin: "24px 0 20px",
  },
  dividerLine: {
    flex: 1,
    height: 1,
    background: "rgba(255, 255, 255, 0.08)",
  },
  dividerText: {
    fontSize: 13,
    color: "rgba(232, 224, 240, 0.4)",
    fontWeight: 500,
    whiteSpace: "nowrap",
  },

  /* ── YouTube URL ── */
  urlRow: {
    display: "flex",
    gap: 10,
    alignItems: "center",
  },
  urlInput: {
    flex: 1,
    border: "1px solid rgba(255, 255, 255, 0.12)",
    borderRadius: 12,
    padding: "11px 14px",
    background: "rgba(255, 255, 255, 0.04)",
    color: "#e8e0f0",
    fontSize: 14,
    fontFamily: "'Outfit', sans-serif",
    outline: "none",
    transition: "border-color 200ms ease, box-shadow 200ms ease",
  },
};
