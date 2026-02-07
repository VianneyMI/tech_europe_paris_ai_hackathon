## Prompt: Stems Separation R&D Agent

You are a new Codex instance exploring audio stem separation tools to split vocals (lyrics) from music (instrumental). Your job is to do hands-on R&D and teach me what you learn.

### Goals
- Evaluate **3 to 5** stem separation tools, **must include Demucs and Spleeter**.
- Produce **3 clean, small apps** (single-file scripts preferred) where I can pass a local audio file path and it outputs **two tracks**:
  - `vocals` (lyrics)
  - `music` (instrumental)
- Share learnings: how stem separation works, each tool's API, dependencies, obstacles, troubleshooting tips.

### Constraints
- Use only tools that can run locally.
- Favor simple CLI or Python scripts.
- Document exact install steps and minimal runtime requirements.
- Aim for a tight feedback loop (speed matters).

### Deliverables
1) **Tool matrix** (3–5 tools)
   - For each tool: summary, install method, model size/quality tradeoffs, speed, license, pros/cons.
   - Must include Demucs + Spleeter; pick at least one additional option (e.g., Open-Unmix, MDX-Net, UVR, etc.).

2) **Three mini-apps (scripts)**  
   Each app should:
   - Accept a local file path argument (wav/mp3).
   - Generate two files: `vocals` and `music` (instrumental).
   - Print output paths and status.
   - Be small and clean; a single file is ideal.
   - Include basic error handling and helpful messages.
   - Provide a short "How to run" section.

3) **Learning notes (teach me)**
   - What stem separation is (short explanation).
   - Common pitfalls and troubleshooting (missing dependencies, model downloads, GPU/CPU concerns, format issues).
   - How to choose a tool (quality vs speed vs simplicity).
   - Any notable obstacles you hit and how you resolved them.

### Expected Process
- Start with Demucs and Spleeter.
- Add 1–3 additional tools based on availability and ease of local use.
- For each tool, validate the minimal "separate vocals + instrumental" workflow.
- If a tool is too heavy or fails, document the failure and move on.

### Output Format
Please deliver results as:
- `TOOLS_OVERVIEW.md`
- `APP_1_<tool>.py` (or `.sh`)
- `APP_2_<tool>.py`
- `APP_3_<tool>.py`
- `LEARNINGS.md`

### Notes
- Focus on practical, runnable code.
- Keep explanations concise and actionable.
- Prefer CPU-compatible defaults, but note GPU options if available.
