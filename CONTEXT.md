# AI Powered Karaoke Project

1. Environment / Constraints

* Duration: 1 weekend hackathon (Sat–Sun)
* Team: Solo Developer
* Goal: working demo > technical depth
* Profile: application engineer, not ML researcher
* Datasets: none (must rely on pretrained models / APIs)

APIs available:

* ~~ElevenLabs (TTS, voice cloning, STT, possibly voice conversion)~~
* [Gradium](https://gradium.ai) (French ElevenLabs-like competitor - we will use this rather than ElevenLabs)

Infra:

* Local dev or lightweight backend (FastAPI / Node acceptable)
* No heavy training pipelines

Legal:

* Demo only, non-commercial
* Explicitly frame as parody / personal use

2. Project Goal (What we are building)

AI Karaoke:

> Take a popular song → replace the singer’s voice with my own → keep timing, melody, and musicality → output a playable karaoke-style track.

Core loop:

1. Input song (audio file or YouTube link)
2. Separate vocals vs instrumental
3. Convert original vocals → target voice
4. Re-sync converted vocals with instrumental
5. Play / export final audio

Non-goals:

* No model training
* No large-scale dataset handling
* No real-time perfection
* No production-grade legality handling

3. MVP Scope (Strict)

Must have

* End-to-end pipeline on one song
* Voice is clearly recognizable as the target speaker
* Latency < a few minutes
* One-click demo (CLI or minimal UI)
* Full UI polish

4. Technical Approach (Preferred)

Pipeline

```sh
Audio Input
 → Vocal Separation
 → Voice Conversion
 → Alignment / Timing
 → Mixdown
 → Playback
```

Likely components

* Vocal separation: Demucs / Spleeter

* Voice conversion:
    * API-based if available (ElevenLabs / Gradium)
    * Otherwise pretrained open-source VC (no training - huggingface models)

* Audio glue:
    * ffmpeg
    * librosa / torchaudio

* Backend orchestration:
    * Python script or FastAPI

* Frontend:
    * React

5. Success Criteria (Hackathon)

* Judges understand the demo in 30 seconds
* The result is **funny / impressive**, not perfect
* Clear narrative:
> “If we can swap voices in music, we can also personalize marketing audio, jingles, brand voices.”

6. Bibliography / References

Use these as implementation references, not theory reading:

* Demucs (vocal separation)
https://github.com/facebookresearch/demucs

* Spleeter (alternative separation)
https://github.com/deezer/spleeter

* ElevenLabs API (voice & audio)
https://docs.elevenlabs.io/

* Gradium API
https://gradium.ai/api_docs.html

* ffmpeg audio processing
https://ffmpeg.org/documentation.html

* librosa (audio alignment / timing)
https://librosa.org/doc/latest/index.html

7. Framing Sentence (use everywhere)

> “AI Karaoke demonstrates how modern voice models can re-render existing audio content with a new speaker identity — opening the door to personalized music, marketing, and branded audio experiences.”