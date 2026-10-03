#!/usr/bin/env python3
"""Render the reviewed crops and permanent redactions in clips.json.

Requires ffmpeg, OpenCV and NumPy. Source files stay outside the published tree.
All coordinates use the manifest's reference-frame size. Output is silent H.264;
source metadata, audio, chapters and source filenames are never copied.
"""
import argparse
import concurrent.futures
import json
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np


def mask_box(mask, timestamp):
    if 'box' in mask:
        return mask['box']
    keys = mask['keyframes']
    return [float(np.interp(timestamp, [k[0] for k in keys], [k[i] for k in keys])) for i in range(1, 5)]


def render(clip, sources, output, coordinate_size, settings):
    if clip['source'] == 'icra' and clip['masks'] and not settings.get('icra_additional_blur', False):
        raise ValueError('ICRA clips must preserve the source blur without additional masks')
    capture = cv2.VideoCapture(str(sources[clip['source']]))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open source for {clip['id']}")
    fps = capture.get(cv2.CAP_PROP_FPS)
    start_frame = math.ceil(clip['start'] * fps)
    end_frame = math.ceil(clip['end'] * fps)
    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    source_w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    sx, sy = source_w / coordinate_size[0], source_h / coordinate_size[1]
    x, y, w, h = clip['crop']
    x, y, w, h = round(x * sx), round(y * sy), round(w * sx), round(h * sy)
    if x < 0 or y < 0 or x + w > source_w or y + h > source_h:
        raise ValueError(f"Crop outside source: {clip['id']}")
    scale = min(settings['max_width'] / w, settings['max_height'] / h, 1)
    out_w, out_h = round(w * scale / 2) * 2, round(h * scale / 2) * 2
    target = output / f"{clip['id']}.mp4"
    temp = output / f".{clip['id']}.tmp.mp4"
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-pixel_format', 'bgr24', '-video_size', f'{out_w}x{out_h}',
               '-framerate', str(fps), '-i', 'pipe:0', '-an', '-map_metadata', '-1',
               '-map_chapters', '-1', '-c:v', 'libx264', '-threads', '2', '-crf', str(clip.get('crf', settings['crf'])),
               '-preset', clip.get('preset', 'medium'), '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
               '-metadata', 'title=', '-metadata', 'comment=', str(temp)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    poster_at = start_frame + min(round(fps), (end_frame - start_frame) // 2)
    try:
        for index in range(start_frame, end_frame):
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Unexpected end of source: {clip['id']}")
            timestamp = index / fps
            for mask in clip['masks']:
                if timestamp < mask.get('start', -1) or timestamp > mask.get('end', float('inf')):
                    continue
                bx, by, bw, bh = mask_box(mask, timestamp)
                left, top = max(0, int(bx * sx)), max(0, int(by * sy))
                right, bottom = min(source_w, math.ceil((bx + bw) * sx)), min(source_h, math.ceil((by + bh) * sy))
                if right <= left or bottom <= top:
                    continue
                # A soft Gaussian patch matches the existing source-video blur.
                margin = max(1, round(mask.get('feather', 5) * sx))
                l, t = max(0, left-margin), max(0, top-margin)
                r, b = min(source_w, right+margin), min(source_h, bottom+margin)
                roi = frame[t:b, l:r]
                sigma = mask.get('sigma', 10) * sx
                hidden = cv2.GaussianBlur(roi, (0, 0), sigmaX=sigma, sigmaY=sigma)
                yy, xx = np.ogrid[t:b, l:r]
                dx = np.maximum(np.maximum(left-xx, xx-right+1), 0)
                dy = np.maximum(np.maximum(top-yy, yy-bottom+1), 0)
                if mask.get('kind') == 'face':
                    radius = np.sqrt(((xx-(left+right)/2)/((right-left)/2+margin))**2
                                     + ((yy-(top+bottom)/2)/((bottom-top)/2+margin))**2)
                    alpha = np.clip((1-radius)/.3, 0, 1)[..., None]
                else:
                    alpha = np.clip(1-np.maximum(dx, dy)/margin, 0, 1)[..., None]
                frame[t:b, l:r] = (hidden*alpha + roi*(1-alpha)).astype(np.uint8)
            frame = cv2.resize(frame[y:y+h, x:x+w], (out_w, out_h), interpolation=cv2.INTER_AREA)
            if index == poster_at:
                cv2.imwrite(str(output / f"{clip['id']}.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            process.stdin.write(frame.tobytes())
    finally:
        capture.release()
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError(f"Encoder failed: {clip['id']}")
    temp.replace(target)
    print(f"Rendered {clip['id']}: {(end_frame-start_frame)/fps:.2f}s, {out_w}x{out_h}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--icra', type=Path)
    parser.add_argument('--traction', type=Path)
    parser.add_argument('--outdoor', type=Path, help='Outdoor footage converted to SDR at a constant frame rate')
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    cv2.setNumThreads(1)
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'scripts/clips.json').read_text())
    clips = [c for c in manifest['clips'] if not args.only or c['id'] in args.only]
    for source in {c['source'] for c in clips}:
        if not vars(args).get(source):
            parser.error(f'--{source} is required for the selected clips')
    output = root / 'assets/video'
    output.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(render, c, vars(args), output, manifest['coordinate_size'], manifest['processing']) for c in clips]
        for future in concurrent.futures.as_completed(futures):
            future.result()


if __name__ == '__main__':
    main()
