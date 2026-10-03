#!/usr/bin/env python3
"""Relabel the 36-second studio animation to match the paper's method figure.

Requires OpenCV, Pillow, NumPy and ffmpeg. Supply the studio MP4 and a Barlow
Medium font explicitly. The animation, camera, callouts and timing are preserved;
only the existing title and footer strips change. No source metadata is retained.
"""
import argparse
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


STAGES = (
    (0, "Flat-Ground Reference.", "INPUT MOTION"),
    (6, "Terrain Adjustment.", "TERRAIN TRANSFORM"),
    (12, "Approach Without Force.", "BEFORE CONTACT"),
    (17, "2 · Hand Lead.", "WRENCH TRANSFORM"),
    (23, "3 · Center-of-Mass Brace.", "WRENCH TRANSFORM"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--font', type=Path, required=True)
    args = parser.parse_args()
    cv2.setNumThreads(1)
    capture = cv2.VideoCapture(str(args.source))
    if not capture.isOpened():
        raise ValueError('Cannot open the studio source')
    dimensions = tuple(int(capture.get(k)) for k in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if dimensions != (1920, 1080) or abs(fps - 25) > .01 or count != 900:
        raise ValueError('Expected the 1920 × 1080, 25 fps, 36-second studio animation')
    output = Path(__file__).resolve().parents[1] / 'assets/video'
    output.mkdir(exist_ok=True)
    target = output / 'reference_transforms.mp4'
    temporary = output / '.reference_transforms.tmp.mp4'
    title_font = ImageFont.truetype(str(args.font), 44)
    label_font = ImageFont.truetype(str(args.font), 22)
    ink, muted, rule = '#08111F', '#53657E', '#DDD1C4'
    headers = []
    for _, title, label in STAGES:
        header = Image.new('RGB', (1920, 119), 'white')
        draw = ImageDraw.Draw(header)
        draw.text((52, 54), title, font=title_font, fill=ink, anchor='lm')
        draw.text((1868, 57), label, font=label_font, fill=muted, anchor='rm')
        draw.line((52, 116, 1868, 116), fill=rule, width=1)
        headers.append(cv2.cvtColor(np.asarray(header), cv2.COLOR_RGB2BGR))
    footer = Image.new('RGB', (1920, 57), 'white')
    draw = ImageDraw.Draw(footer)
    draw.line((52, 0, 1868, 0), fill=rule, width=1)
    draw.text((52, 30), 'Kinematic illustration · illustrative contact and load', font=label_font, fill=muted, anchor='lm')
    draw.text((1868, 30), 'BRACE · Reference synthesis', font=label_font, fill=muted, anchor='rm')
    footer = cv2.cvtColor(np.asarray(footer), cv2.COLOR_RGB2BGR)
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-pixel_format', 'bgr24', '-video_size', '1920x1080', '-framerate', '25',
               '-i', 'pipe:0', '-an', '-map_metadata', '-1', '-map_chapters', '-1',
               '-c:v', 'libx264', '-threads', '4', '-crf', '18', '-preset', 'medium',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(temporary)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for i in range(count):
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError('Unexpected end of studio animation')
            stage = max(j for j, (start, _, _) in enumerate(STAGES) if i / fps >= start)
            frame[:119] = headers[stage]
            frame[1023:] = footer
            if i == 525:
                cv2.imwrite(str(output / 'reference_transforms.jpg'), frame, [cv2.IMWRITE_JPEG_QUALITY, 94])
            process.stdin.write(frame.tobytes())
    finally:
        capture.release()
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError('Reference animation encoder failed')
    temporary.replace(target)
    print('Rendered reference_transforms: 36 seconds, 1080p, five figure-aligned stages.')


if __name__ == '__main__':
    main()
