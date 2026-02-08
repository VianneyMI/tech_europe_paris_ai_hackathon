export interface LyricsTimestamp {
  text: string;
  start_s: number;
  stop_s: number;
}

export interface ProcessResponse {
  job_id: string;
  lyrics: string;
  lyrics_with_timestamps: LyricsTimestamp[];
  vocals_url: string;
  instrumental_url: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function processAudio(file: File): Promise<ProcessResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/process`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body: unknown = await response.json();
      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof (body as { detail: unknown }).detail === "string"
      ) {
        detail = (body as { detail: string }).detail;
      }
    } catch {
      // Ignore JSON parse failures and keep default error.
    }
    throw new Error(detail);
  }

  return (await response.json()) as ProcessResponse;
}

export async function fetchDemo(): Promise<ProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/demo`);
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body: unknown = await response.json();
      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof (body as { detail: unknown }).detail === "string"
      ) {
        detail = (body as { detail: string }).detail;
      }
    } catch {
      // Ignore JSON parse failures and keep default error.
    }
    throw new Error(detail);
  }

  return (await response.json()) as ProcessResponse;
}

export function toAbsoluteAudioUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
}
