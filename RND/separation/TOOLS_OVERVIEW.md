# Stem Separation Tools Overview

## Quick matrix

| Tool | Local install method | Model/quality tradeoff | CPU speed (relative) | License | Pros | Cons |
|---|---|---|---|---|---|---|
| Demucs (required) | `pip/uv install demucs` | Newer hybrid transformer models often best vocal quality; larger models are slower/heavier | Medium-slow | MIT | High quality vocals/instrumental split; strong community usage | First run model download; slower on CPU |
| Spleeter (required) | `pip/uv install spleeter` | 2/4/5 stem models; 2-stem is fastest and usually enough for karaoke-like split | Fast-medium | MIT | Very simple CLI and predictable output layout | TensorFlow dependency friction on some Python/CUDA combos |
| Open-Unmix | `pip/uv install openunmix` | 4-stem model; good baseline quality, often slightly behind top Demucs variants | Medium | MIT | Straightforward CLI (`umx`), easy local use | Need to recombine stems for a single `music` track |
| UVR / MDX-Net family | Usually GUI (Ultimate Vocal Remover) or third-party wrappers | MDX models can be high quality for vocals; model choice matters heavily | Medium (varies by model) | Mixed (tool + model dependent) | Strong practical quality with the right model | Less uniform CLI/API; automation can be inconsistent |

## R&D verdict

- Best quality-first default: **Demucs**.
- Best simplest-two-stem workflow when environment matches: **Spleeter**.
- Best pragmatic pure-Python CLI baseline: **Open-Unmix**.
- For MDX/UVR, quality can be strong, but reproducible scripted setup is less standardized.

## Minimal requirements (common)

- Python 3.10+ (some stacks are stricter).
- `ffmpeg` on `PATH` for robust mp3 decode/encode paths.
- Enough disk for model downloads (hundreds of MB possible).
- CPU works for all apps in this folder; GPU is optional.
