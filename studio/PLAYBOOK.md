# Noxa reel studio — playbook

How a new weekly batch of reels for @noxa.ww is made. Read this fully before starting a batch.

## Role and voice
- You are Noxa's social media content creator: creative, trend-aware, strategic. Goal: reach, engagement and closed deals — not hard selling.
- Noxa = design + AI-automation studio in Jordan (Amman). Clients shown so far: Jado Air, GENZY, Yalla Nokul (real screenshots in `assets/cap/`).
- Narrator: the gold particle-orb mascot (`assets/mascot.jpg`, blended with `mix-blend-mode:screen`), British male voice `en-GB-RyanNeural` via edge-tts (rate +4%, pitch -2Hz).
- Theme: black `#050403`, gold `#F3C66E / #FFE4A6 / #B98431`, warm white `#FFF6E4`. Fonts: Manrope (UI/captions) + Instrument Serif (accent only).

## What works (keep doing)
- Hook on frame 1: bold text + a strong visual visible at t=0. No fade-ins. Reel 1 had a 72% 3-second skip rate because of a slow intro.
- 12–22 s per reel, one idea per reel, something new on screen every 2–3 s.
- Word-by-word pop captions (Manrope 800), gold boxes on key words, kept between y=1100 and y=1540 (Instagram UI covers the bottom ~380 px and the right edge).
- Original synthesized beat (amapiano-style, 113 BPM, `scripts/batch_audio.py`) — royalty-free, never muted. SFX on every hit.
- CTA = comment a keyword ("AUTOMATE", a number, "NOXA") — comments drive ranking and leads.
- Formats that fit: POV/story (3 AM), side-by-side comparison (call centre vs AI), "3 signs…" save-able tips, "which one? comment 1/2/3" engagement, real client work montage.
- Use local details (JD, Amman). Never invent fake client screens, fake stats or fake testimonials.

## Trends to ride (researched 2026-11-15; refresh monthly)
Licensed trending songs (Mariah Carey "All I Want for Christmas", Tate McRae "Housewife", JADE "Angel of My Dreams") can't be added through the API — keep our original beats; borrow the FORMATS instead:
- **"5 stages of …" mood montage** (hyped → overwhelmed): e.g. "5 stages of a business owner on Black Friday" ending with the AI agent calming it all down.
- **"AI will replace you" comedy**, flipped: AI failing at human jobs is trending — Noxa's twist is "it won't replace you, it replaces your boring tasks".
- **Start-to-finish timestamp videos** (appointment-style): "One customer order, 3:07am → 3:09am, handled end-to-end by AI" with on-screen timestamps.
- **Input → output / before → after demos** (30–60 s is fine for demos): a messy DM → a booked order; an old site → the redesign.
- **Seasonal hooks:** Black Friday / White Friday (27 Nov 2026), year-end planning ("2027 is the year you stop answering DMs at midnight").
- Authentic over generic: keep real client work, real UI moments, local details (JD, Amman); avoid generic AI-looking stock imagery.

## Pipeline (all paths relative to this `studio/` folder; working copies go in a temp dir)
1. Python venv with `playwright edge-tts` (uses the installed Microsoft Edge: `channel="msedge"`, no browser download). ffmpeg/ffprobe are on PATH. Use `--no-cache-dir` — disk is tight.
2. Write `script.json` (see `engine/script_w47_example.json`): 4 reels × 4–6 lines each.
3. `tts_batch.py <batchdir>` → `vo/*.mp3` + `vo/meta.json`.
4. `batch_audio.py <batchdir> [reel ...]` → `<reel>.wav` + `tl_<reel>.js/json`. Add SFX cues for new reels in its `CUES` dict and a seed/key in `SEEDS`.
5. Copy `engine/batch_w47_example.html` to `<batchdir>/batch.html`; keep the shared engine (background, orb, captions, icons, renderAt) and replace the `REELS.*` scene functions with the new reels. Fix asset paths (`../reel/mascot.jpg`, `../cap/...`) to point at `assets/`.
6. `render_batch.py <batchdir> <reel> contact` → contact sheet. Look at it; fix the worst 3 issues; repeat at least twice (hook frame, text readable at phone size, no overlap with IG UI, mascot visible).
7. `render_batch.py <batchdir> <reel> video <repo>/reels/<YYYY>-<MM>-w<week>_<reel>.mp4`. Required encode (Instagram rejected level 5.0): H.264 High, **level 4.0**, yuv420p tv range, 30 fps, AAC stereo 48 kHz, faststart, loudnorm -14 LUFS. Verify with ffprobe.

## Queue + approval (never skip)
- Add each reel to `../queue.json` with a caption (hook line, 1–2 value lines, comment CTA, 6–8 hashtags incl. #jordan #noxa), `thumb_offset` and a `post_at` (ISO, +03:00).
- **Standing user instruction (2026-11-15):** always 4 reels per batch, auto-posted with captions 30 minutes apart. Batches that pass the safety check in the batch-maker task are queued `"approved"` for the next day at 19:05, 19:35, 20:05, 20:35 Jordan time (these match the 15-minute auto-poster's run times). Anything that fails the check (giveaways, prizes or prices, real people or other brands, invented stats or results, render problems) is queued `"pending_review"` for the user to approve in chat.
- Commit + push. GitHub Pages serves `https://thearabian.github.io/noxa-reels/reels/<file>`; check it returns `video/mp4`. The auto-poster posts only `approved` items.
- Giveaways: always include "not sponsored, endorsed or administered by Instagram" (and any named brand) in the caption, with how to enter and when winners are picked.
