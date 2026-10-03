#!/usr/bin/env python3
"""Serve the site locally with HTTP byte ranges, for previewing the videos.

`python3 -m http.server` answers every request with the whole file over HTTP/1.0. A browser that
asks for a clip's header to draw its poster then has to download the entire clip, for each of the
page's twenty-odd players, on a fresh connection each time, which is why the page used to take so
long to settle. This handler answers `Range` requests with `206 Partial Content`, keeps connections
open (HTTP/1.1), and sends no-cache headers so a reload always shows the current files.

    python3 scripts/serve.py            # http://localhost:8000
    python3 scripts/serve.py 8917
"""

from __future__ import annotations

import os
import re
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RANGE = re.compile(r"bytes=(\d*)-(\d*)")


class RangeHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self) -> None:
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_head(self):
        match = RANGE.fullmatch(self.headers.get("Range", "").strip()) if "Range" in self.headers else None
        path = self.translate_path(self.path)
        if match is None or os.path.isdir(path) or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        first, last = match.groups()
        if first == "" and last == "":
            return super().send_head()
        if first == "":  # suffix range: the last N bytes
            start, end = max(size - int(last), 0), size - 1
        else:
            start = int(first)
            end = min(int(last), size - 1) if last else size - 1
        if start >= size or start > end:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        f = open(path, "rb")
        try:
            f.seek(start)
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Last-Modified", self.date_time_string(int(os.stat(path).st_mtime)))
            self.end_headers()
        except Exception:
            f.close()
            raise
        self._range_remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile) -> None:
        remaining = getattr(self, "_range_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        self._range_remaining = None
        while remaining > 0:
            chunk = source.read(min(remaining, 1 << 16))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

    def log_message(self, fmt, *args) -> None:
        return  # quiet; the browser's network panel is the better log


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    with ThreadingHTTPServer(("127.0.0.1", port), RangeHandler) as httpd:
        print(f"Serving {root} at http://127.0.0.1:{port}/  (Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
