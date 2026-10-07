# BRACE project page

Project page for **BRACE: Adapting Whole-Body References for Force and Terrain Aware Humanoid Motion Tracking**, from Multiply Labs, Brown University and the University of New Mexico.

Live at <https://multiplylabs.github.io/brace/>. Every push to `main` deploys through GitHub Actions.

This is the **named** project page. An anonymous copy exists separately for double-blind review; nothing in this repository links to it, and edits are never shared between the two repositories.

## Layout

```
index.html                    the page
assets/css/site.css           styles and design tokens
assets/js/site.js             turns placeholders on once their files exist; mounts players as they near the viewport
scripts/serve.py              local preview server with byte-range support
assets/paper.pdf              the paper (not yet added; the button shows "Soon" until it is)
assets/img/                   figures exported from the paper
assets/video/                 videos (<slot>.mp4) and optional posters (<slot>.jpg)
.github/workflows/deploy.yml  deploy to GitHub Pages
```

The site is plain HTML and CSS with no build step. The workflow copies `index.html` and `assets/` into the Pages artifact. README, CLAUDE.md and scripts are not published to the site.

## Preview locally

```sh
python3 scripts/serve.py 8000   # then open http://localhost:8000
```

Use a server, not `file://`. The placeholder logic checks whether files exist with `fetch`, which does not work on `file://` pages.

Use `scripts/serve.py` rather than `python3 -m http.server`. The built-in server has no byte-range support and speaks HTTP/1.0, so a browser asking for a clip's header ends up downloading the whole clip, for every player, on a fresh connection each time. GitHub Pages serves ranges, so the live site never had this problem; only local previews did.

## Adding content

Every placeholder switches on as soon as its file is committed. No HTML changes are needed except for the code link.

### Paper and appendix

**Read paper** links to the arXiv entry, <https://arxiv.org/abs/2610.07052>, as does the footer's
arXiv link. There is no PDF in the repo. When an appendix is ready, add it as `assets/appendix.pdf`
and add its link next to **Read paper**.

### Live demo

The **Live demo** button is a `data-soon` placeholder for now. Its href already points at the
browser demo, <https://multiplylabs.github.io/robogym-online/>; remove the `data-soon` attribute
(and add `target="_blank" rel="noopener"`) to switch it on, and add a matching nav link.

### Code

When the code repo is ready, add its link next to **Read paper** in `index.html`.

### Videos

The page contains 20 distinct demonstrations, a reference-transformation animation, and a silent hero playlist. Each demonstration
appears once in the galleries; only the teaser reuses clips.
The teaser always starts with syringe insertion, followed by kettlebell squats and a ramp walk,
then outdoor bicep curls. It repeats that sequence. The title and gray overlay stay in place.
The outdoor demo uses the first 30 seconds of the submission video; the teaser uses a separate
4–20-second cut of that sequence. Both crop out the title along the top edge and retain
the source blur treatment without additions.
Demonstrations and figures lead the page. Baseline comparisons precede applications;
the method animation and full method figure follow. The abstract, training details,
and quantitative results are expandable.
The original source videos stay outside this repository. Only the cropped and redacted H.264
exports and their posters are published. All exports omit audio, source metadata, and chapters.
Captions, comparison labels, loads, and source playback speeds appear in the HTML beneath the
players. Applications start with VLA execution, then interactive control and remote teleoperation.
Both remote players prominently mark the approximately 1,000-mile
distance between the operator and robot.

| Clip | Section | Description |
|---|---|---|
| `cart_push_slope` | Hardware | Cart push on slope |
| `syringe_insertion` | Hardware | Syringe insertion |
| `barbell_lift` | Hardware | Barbell lifting |
| `winch_rotation` | Hardware | Winch rotation |
| `torque_control` | Hardware | Torque from two viewpoints |
| `outdoor_squat_ramp` | Hardware | Kettlebell squats followed by a ramp walk (0–30 s) |
| `outdoor_squat_teaser` | Teaser only | Shorter squat-to-ramp sequence (4–20 s) |
| `outdoor_bicep` | Hardware | Outdoor bicep curls |
| `kettlebell_carry` | Hardware | Indoor kettlebell carrying |
| `kettlebell_squat` | Hardware | Indoor kettlebell squats |
| `resisted_squat` | Hardware | Force exertion while squatting |
| `force_gauge` | Hardware | Measured hand force |
| `terrain_manipulation` | Hardware | Terrain-aware tabletop motion |
| `comparison_box` | Comparisons | Box-lifting comparison |
| `comparison_slope` | Comparisons | Slope-traversal comparison |
| `comparison_rows` | Comparisons | Resistance-band rows |
| `comparison_lateral` | Comparisons | Lateral resistance-band exercise |
| `vla_execution` | Applications | Autonomous VLA execution |
| `teleop_gamepad` | Applications | Interactive directional control |
| `teleop_remote` | Applications | Remote barbell lifting (TRACTION 1:48–1:58, uncropped) |
| `teleop_remote_slope` | Applications | Remote slope traversal (TRACTION 2:00–2:09, uncropped) |
| `reference_transforms` | Method | Terrain adjustment, contact, hand lead, and COM brace |

The edit decisions live in `scripts/clips.json`: source intervals, crop rectangles, masks,
and optional per-clip `crf` and `preset` settings to keep longer exports compact.
Submission-video clips retain the source video's existing blur with **no additional blur**.
CoRL clips use small, feathered Gaussian masks for exposed faces and selected labels, matching
the submission-video treatment. VR headset operators receive no added face blur. Coordinates use a
960 × 540 reference frame; timed keyframes follow moving subjects. Exports preserve up to
1080p source resolution without upscaling. The hero uses these prepared clips; no original
footage is copied to the published tree. The outdoor curl clip uses the requested 16–25-second
interval, with tracked blur on the background sign and street number.

To reproduce the videos, install `opencv-python-headless` and `numpy` in a local environment,
and ensure `ffmpeg` is on PATH. First convert HDR outdoor footage to SDR at 30 fps
(the following command requires FFmpeg with `libplacebo` and Vulkan support), then pass
the three source files explicitly:

```sh
ffmpeg -init_hw_device vulkan=vk -filter_hw_device vk -i path/to/outdoor-source.mov \
  -map 0:v:0 -vf 'libplacebo=colorspace=bt709:color_primaries=bt709:color_trc=bt709:format=yuv420p,format=yuv420p,fps=30' \
  -an -map_metadata -1 -map_chapters -1 -c:v libx264 -crf 17 path/to/outdoor-sdr.mp4
python scripts/render-clips.py --submission path/to/submission-video.mp4 --traction path/to/traction-video.mp4 --outdoor path/to/outdoor-sdr.mp4
```

Use `--only clip_name` to render a single clip; only that clip's source argument is required.
After any edit, visually check the entire affected
clip, including its first and last frames. The hero automatically uses the updated clip. Posters use the same treatment as their clips. Keep individual
demonstrations below 20 MB.

Players loop silently while visible and pause off screen. Reduced-motion preferences disable
automatic playback, and controls remain available for manual playback. The hero has a separate
Play/Pause button.

### Reference-transform animation

The method player uses the 36-second studio visibility animation. Five chapter buttons
seek to the flat-ground reference (0 s), terrain adjustment (6 s), approach (12 s),
hand lead (17 s), and COM brace (23 s). The short explanation and highlighted region
of the full method figure follow the playhead. Figure callouts retain their paper
numbering: ① feasibility limits, ② hand lead, ③ COM brace. The approach chapter
connects the no-contact pose to the feasibility limits; the animation is a kinematic
illustration, not a numerical validation of those limits.

`scripts/render-reference.py` replaces only the source animation's title/footer strips,
preserving its poses, camera, in-scene labels, color coding, and timing. It exports
silent 1080p H.264 with no source metadata or chapters, plus a poster. Reproduce with
OpenCV, NumPy, Pillow, FFmpeg, and a Barlow Medium TTF:

```sh
python scripts/render-reference.py --source path/to/studio_visibility_refinement.mp4 --font path/to/Barlow-Medium.ttf
```

The page is static HTML, CSS and JavaScript and requires no build step.

## Camera-ready

When the paper is accepted: add `assets/paper.pdf`, the BibTeX, and the camera-ready and code links, and update the footer venue string.
