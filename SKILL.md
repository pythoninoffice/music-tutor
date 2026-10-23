---
name: music tutor
description: >-
  Use when given sheet music (image/PDF) or a song name to render it as audio in
  an instrument, make jianpu notation, or build falling-note piano tutorial
  videos with fingering, including cartoon/toon 3D-hand portrait videos with
  themed visuals.
---
# Sheet music → instrument audio + tutorial videos

Reference implementation (Axel F example) lives in `examples/` beside this file: `make.py`, `piano.py`, `video.py`, `cello_video.py`. Copy and adapt; don't start from scratch.

## 0. Setup (box, once)
- `sudo apt-get install -y fluidsynth fluid-soundfont-gm` (soundfont `/usr/share/sounds/sf2/FluidR3_GM.sf2`). Re-check after box resets; it can go missing.
- `pip install --user --break-system-packages mido cairosvg pdf2image`; poppler-utils for `pdftoppm`.

## 1. Get and transcribe the sheet
- Download the PDF. Some sheet sites return a captcha HTML page instead of a PDF: check the file type/size. If blocked, ask the user to attach it, or try a Wayback Machine copy.
- `pdftoppm -r 300 -png` pages; crop each system (RH/LH staff) into its own image and zoom to read. OMR tools tend to crash; transcribe by eye, system by system.
- Record key, time signature, tempo changes (accel/rit), repeats, ottava marks, ties. Encode bars in a `score.py`; check each bar sums to its meter; expand repeats.
- Output one notes JSON: per note start (s), length, pitch, hand, finger, bar, with a ~3 s lead-in. Everything (MIDI, audio, video) derives from it so sync is guaranteed.
- Tell the user which bars are simplified or uncertain.

## 2. Number (jianpu) sheet (optional)
- 1 = tonic; dots = octave; underlines = ½/¼ beat; render SVG → PNG via cairosvg with a legend.

## 3. Audio
- mido MIDI with the tempo map; GM program (piano 0, cello 42, ...); FluidSynth render; normalize with ffmpeg loudnorm (~-16 LUFS, peak ~-1.5 dB). Send audio first and let the user approve before video.
- Slow practice version = re-render at the scaled tempo (only if the user wants one).

## 4. Fingering
- Generate fingering per hand (1=thumb..5=pinky): no thumb on black keys, thumb-under/cross-over for runs, same finger on repeats. Write `fingering.md` bar by bar and flag awkward spots.

## 5a. Simple 2D falling-notes video
- PIL frames piped to ffmpeg (1280x720 or 1080x1920, 30 fps), falling bars with finger number + note letter, keyboard lights up, hands colored differently. Mux the same audio.

## 5b. Cartoon (toon) 3D-hand portrait video (preferred look)
- Hands: Blender (portable 4.x LTS; Cycles OptiX on an NVIDIA GPU) with MPFB/MakeHuman CC0 hands. Solve finger joints so each fingertip lands on its key per the notes JSON; relaxed (not clawed) resting pose; keep the thumb visible on thumb-under.
- Render hands only, transparent background, top-down camera that follows the hands, with per-pixel hand ID + depth passes (needed for outlines).
- Composite in Python (PIL/numpy): cel shading, a bold dark ink outline (~5 px at 1080 wide) around each hand including the edge where one hand overlaps the other, a subtle warm/cool tint difference between hands, inked keyboard, falling bars with letters + finger numbers, key glow, title, bar label (clamp to last bar), legend. Use enough precision in the hand frames to avoid grainy speckles.
- Portrait 1080x1920 for phones; landscape optional.
- Theme variants by flag in the compositor, e.g. starry night (default), or an anime/show theme (palette, background grid, HUD bars, section caution labels, title card in the show's typography; use OFL fonts).
- Workflow: make 2-3 stills (intro, a dense section, a hand-overlap moment) and get approval, then render full.

## 6. Rendering and robustness
- Heavy rendering goes on the user's own GPU PC if available; the box CPU is slow (~1 s/frame on an RTX 3080 vs much slower on the box).
- Launch long PC renders as detached background processes (e.g. PowerShell `Start-Process`) so an interrupted session doesn't kill them; resume by reusing finished frames.
- Don't blanket-kill all `python` processes on the user's PC (other services run there).
- Keep scripts + notes JSON copied on the PC too; the box can be reset.
- Verify: duration, A/V sync by cross-correlating against the source WAV at several points (target ≤5 ms), and spot-check frames.

## 7. Deliver
- Attach MP3/MP4s. Also make a phone-friendly copy (`-vf scale=720:-2 -c:v libx264 -profile:v baseline -pix_fmt yuv420p -crf 28 -movflags +faststart`); large/high-profile files may not open on phones.
- Say where full-quality files are saved and list known visual issues (e.g. a hand off-screen in wide passages).
