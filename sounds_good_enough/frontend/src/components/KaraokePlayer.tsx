import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { JSX } from "react";

import type { LyricsTimestamp } from "../api/client";
import { toAbsoluteAudioUrl } from "../api/client";
import "./KaraokePlayer.css";

interface KaraokePlayerProps {
  instrumentalUrl: string;
  timestamps: LyricsTimestamp[];
}

interface KaraokeLineWord {
  segment: LyricsTimestamp;
  wordIndex: number;
}

interface KaraokeLine {
  id: string;
  start_s: number;
  stop_s: number;
  words: KaraokeLineWord[];
}

const DEFAULT_MAX_WORDS_PER_LINE = 8;
const DEFAULT_GAP_THRESHOLD_S = 0.9;
const MAX_LOCAL_SCAN_STEPS = 8;

export function groupSegmentsIntoLines(
  segments: LyricsTimestamp[],
  maxWordsPerLine = DEFAULT_MAX_WORDS_PER_LINE,
  gapThresholdS = DEFAULT_GAP_THRESHOLD_S,
): KaraokeLine[] {
  if (segments.length === 0) {
    return [];
  }

  const lines: KaraokeLine[] = [];
  let currentWords: KaraokeLineWord[] = [];

  const flushCurrentLine = (): void => {
    if (currentWords.length === 0) {
      return;
    }

    const first = currentWords[0];
    const last = currentWords[currentWords.length - 1];
    lines.push({
      id: `${first.wordIndex}-${last.wordIndex}`,
      start_s: first.segment.start_s,
      stop_s: last.segment.stop_s,
      words: currentWords,
    });
    currentWords = [];
  };

  for (let i = 0; i < segments.length; i += 1) {
    const segment = segments[i];
    const previous = currentWords[currentWords.length - 1]?.segment;
    const hasLargeGap = previous ? segment.start_s - previous.stop_s >= gapThresholdS : false;
    const reachedWordLimit = currentWords.length >= maxWordsPerLine;

    if (reachedWordLimit || hasLargeGap) {
      flushCurrentLine();
    }

    currentWords.push({ segment, wordIndex: i });
  }

  flushCurrentLine();
  return lines;
}

function findRightmostStartIndex(items: Array<{ start_s: number }>, currentTime: number): number {
  let low = 0;
  let high = items.length - 1;
  let result = -1;

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    if (items[mid].start_s <= currentTime) {
      result = mid;
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }

  return result;
}

function findActiveWordIndex(
  segments: LyricsTimestamp[],
  currentTime: number,
  hintIndex: number,
): number {
  if (segments.length === 0) {
    return -1;
  }

  if (hintIndex >= 0 && hintIndex < segments.length) {
    const hinted = segments[hintIndex];
    if (hinted.start_s <= currentTime && currentTime < hinted.stop_s) {
      return hintIndex;
    }

    let idx = hintIndex;
    let steps = 0;

    if (currentTime >= hinted.stop_s) {
      while (
        idx + 1 < segments.length &&
        segments[idx + 1].start_s <= currentTime &&
        steps < MAX_LOCAL_SCAN_STEPS
      ) {
        idx += 1;
        steps += 1;
        if (segments[idx].start_s <= currentTime && currentTime < segments[idx].stop_s) {
          return idx;
        }
      }
    } else if (currentTime < hinted.start_s) {
      while (idx - 1 >= 0 && currentTime < segments[idx].start_s && steps < MAX_LOCAL_SCAN_STEPS) {
        idx -= 1;
        steps += 1;
        if (segments[idx].start_s <= currentTime && currentTime < segments[idx].stop_s) {
          return idx;
        }
      }
    }
  }

  const candidate = findRightmostStartIndex(segments, currentTime);
  if (candidate === -1) {
    return -1;
  }

  return currentTime < segments[candidate].stop_s ? candidate : -1;
}

function findActiveLineIndex(lines: KaraokeLine[], currentTime: number, hintIndex: number): number {
  if (lines.length === 0) {
    return -1;
  }

  if (hintIndex >= 0 && hintIndex < lines.length) {
    const hinted = lines[hintIndex];
    if (hinted.start_s <= currentTime && currentTime < hinted.stop_s) {
      return hintIndex;
    }

    let idx = hintIndex;
    let steps = 0;

    if (currentTime >= hinted.stop_s) {
      while (idx + 1 < lines.length && lines[idx + 1].start_s <= currentTime && steps < MAX_LOCAL_SCAN_STEPS) {
        idx += 1;
        steps += 1;
        if (lines[idx].start_s <= currentTime && currentTime < lines[idx].stop_s) {
          return idx;
        }
      }
    } else if (currentTime < hinted.start_s) {
      while (idx - 1 >= 0 && currentTime < lines[idx].start_s && steps < MAX_LOCAL_SCAN_STEPS) {
        idx -= 1;
        steps += 1;
        if (lines[idx].start_s <= currentTime && currentTime < lines[idx].stop_s) {
          return idx;
        }
      }
    }
  }

  const candidate = findRightmostStartIndex(lines, currentTime);
  if (candidate === -1) {
    return -1;
  }

  return currentTime < lines[candidate].stop_s ? candidate : -1;
}

function getLineClassName(activeLineIndex: number, lineCursorIndex: number, lineIndex: number): string {
  if (activeLineIndex === -1) {
    if (lineCursorIndex === -1) {
      return "karaoke-line karaoke-line--future";
    }
    return lineIndex <= lineCursorIndex ? "karaoke-line karaoke-line--past" : "karaoke-line karaoke-line--future";
  }

  if (lineIndex < activeLineIndex) {
    return "karaoke-line karaoke-line--past";
  }

  if (lineIndex === activeLineIndex) {
    return "karaoke-line karaoke-line--active";
  }

  return "karaoke-line karaoke-line--future";
}

export default function KaraokePlayer({ instrumentalUrl, timestamps }: KaraokePlayerProps): JSX.Element {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafIdRef = useRef<number | null>(null);
  const lastWordIndexRef = useRef<number>(-1);
  const lastLineIndexRef = useRef<number>(-1);
  const lineElementsRef = useRef<Array<HTMLDivElement | null>>([]);

  const [activeWordIndex, setActiveWordIndex] = useState<number>(-1);
  const [activeLineIndex, setActiveLineIndex] = useState<number>(-1);
  const [lineCursorIndex, setLineCursorIndex] = useState<number>(-1);

  const lines = useMemo(() => groupSegmentsIntoLines(timestamps), [timestamps]);
  const activeWordIndexRef = useRef<number>(activeWordIndex);
  const activeLineIndexRef = useRef<number>(activeLineIndex);
  const lineCursorIndexRef = useRef<number>(lineCursorIndex);

  useEffect(() => {
    activeWordIndexRef.current = activeWordIndex;
  }, [activeWordIndex]);

  useEffect(() => {
    activeLineIndexRef.current = activeLineIndex;
  }, [activeLineIndex]);

  useEffect(() => {
    lineCursorIndexRef.current = lineCursorIndex;
  }, [lineCursorIndex]);

  useEffect(() => {
    lineElementsRef.current = lineElementsRef.current.slice(0, lines.length);
  }, [lines]);

  const syncFromCurrentTime = useCallback((): void => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const currentTime = audio.currentTime;
    const nextLineCursorIndex = findRightmostStartIndex(lines, currentTime);

    const nextWordIndex = findActiveWordIndex(timestamps, currentTime, lastWordIndexRef.current);
    const nextLineIndex = findActiveLineIndex(lines, currentTime, lastLineIndexRef.current);

    lastWordIndexRef.current = nextWordIndex;
    lastLineIndexRef.current = nextLineIndex;

    if (nextWordIndex !== activeWordIndexRef.current) {
      activeWordIndexRef.current = nextWordIndex;
      setActiveWordIndex(nextWordIndex);
    }

    if (nextLineIndex !== activeLineIndexRef.current) {
      activeLineIndexRef.current = nextLineIndex;
      setActiveLineIndex(nextLineIndex);
    }

    if (nextLineCursorIndex !== lineCursorIndexRef.current) {
      lineCursorIndexRef.current = nextLineCursorIndex;
      setLineCursorIndex(nextLineCursorIndex);
    }
  }, [lines, timestamps]);

  const stopSyncLoop = useCallback((): void => {
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
  }, []);

  const syncLoop = useCallback((): void => {
    syncFromCurrentTime();
    if (!audioRef.current?.paused) {
      rafIdRef.current = requestAnimationFrame(syncLoop);
    } else {
      rafIdRef.current = null;
    }
  }, [syncFromCurrentTime]);

  const startSyncLoop = useCallback((): void => {
    if (rafIdRef.current !== null) {
      return;
    }
    rafIdRef.current = requestAnimationFrame(syncLoop);
  }, [syncLoop]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const handlePlay = (): void => startSyncLoop();
    const handlePause = (): void => stopSyncLoop();
    const handleEnded = (): void => {
      stopSyncLoop();
      syncFromCurrentTime();
    };
    const handleSeeked = (): void => syncFromCurrentTime();

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("seeked", handleSeeked);

    return () => {
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("seeked", handleSeeked);
      stopSyncLoop();
    };
  }, [startSyncLoop, stopSyncLoop, syncFromCurrentTime]);

  useEffect(() => {
    lastWordIndexRef.current = -1;
    lastLineIndexRef.current = -1;
    setActiveWordIndex(-1);
    setActiveLineIndex(-1);
    setLineCursorIndex(-1);
    syncFromCurrentTime();
  }, [instrumentalUrl, syncFromCurrentTime, timestamps]);

  useEffect(() => {
    if (activeLineIndex < 0) {
      return;
    }

    const activeLineElement = lineElementsRef.current[activeLineIndex];
    activeLineElement?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [activeLineIndex]);

  return (
    <section className="karaoke-player" aria-label="Karaoke player">
      <h3 className="karaoke-title">Karaoke</h3>
      <audio ref={audioRef} controls src={toAbsoluteAudioUrl(instrumentalUrl)} className="karaoke-audio" />

      <div className="karaoke-lyrics" aria-live="polite">
        {lines.length === 0 ? (
          <p className="karaoke-empty">No timestamp segments returned.</p>
        ) : (
          lines.map((line, lineIndex) => (
            <div
              key={line.id}
              className={getLineClassName(activeLineIndex, lineCursorIndex, lineIndex)}
              ref={(element) => {
                lineElementsRef.current[lineIndex] = element;
              }}
            >
              {line.words.map((word) => (
                <span
                  key={`${line.id}-${word.wordIndex}`}
                  className={
                    word.wordIndex === activeWordIndex
                      ? "karaoke-word karaoke-word--active"
                      : "karaoke-word"
                  }
                >
                  {word.segment.text}
                </span>
              ))}
            </div>
          ))
        )}
      </div>
    </section>
  );
}
