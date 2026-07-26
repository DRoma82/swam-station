#!/usr/bin/env python3
"""Receive Sonarr/Radarr import webhooks and send concise Telegram notifications."""

from __future__ import annotations

import html
import json
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = os.getenv("MEDIA_IMPORT_NOTIFIER_HOST", "0.0.0.0")
PORT = int(os.getenv("MEDIA_IMPORT_NOTIFIER_PORT", "8080"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("MEDIA_IMPORT_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("MEDIA_IMPORT_TELEGRAM_CHAT_ID", "")
WEBHOOK_TOKEN = os.getenv("MEDIA_IMPORT_WEBHOOK_TOKEN", "")
JELLYFIN_NOTE = os.getenv("MEDIA_IMPORT_JELLYFIN_NOTE", "Available in Jellyfin soon")

IMPORT_EVENTS = {
    "Download",
    "DownloadFolderImported",
    "MovieFileImported",
    "EpisodeFileImported",
}


def pick(data: dict[str, Any], *paths: str, default: str = "") -> str:
    for path in paths:
        cur: Any = data
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return str(cur)
    return default


def nested(data: dict[str, Any], path: str) -> dict[str, Any]:
    cur: Any = data
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part, {})
        else:
            return {}
    return cur if isinstance(cur, dict) else {}


def first_non_empty(*values: str) -> str:
    return next((v for v in values if v), "")


def quality(data: dict[str, Any]) -> str:
    q = first_non_empty(
        pick(data, "episodeFile.quality.quality.name"),
        pick(data, "movieFile.quality.quality.name"),
        pick(data, "quality.quality.name"),
        pick(data, "quality.name"),
    )
    revision = first_non_empty(
        pick(data, "episodeFile.quality.revision.version"),
        pick(data, "movieFile.quality.revision.version"),
    )
    if revision and revision != "1":
        return f"{q} v{revision}" if q else f"v{revision}"
    return q


def release_group(data: dict[str, Any]) -> str:
    return first_non_empty(
        pick(data, "episodeFile.releaseGroup"),
        pick(data, "movieFile.releaseGroup"),
        pick(data, "releaseGroup"),
    )


def link_line(label: str, url: str) -> str:
    return f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>'


def tvdb_url(tvdb_id: str, kind: str = "series") -> str:
    if kind == "episode":
        return f"https://thetvdb.com/dereferrer/episode/{urllib.parse.quote(tvdb_id)}"
    return f"https://thetvdb.com/dereferrer/series/{urllib.parse.quote(tvdb_id)}"


def imdb_url(imdb_id: str) -> str:
    return f"https://www.imdb.com/title/{urllib.parse.quote(imdb_id)}/"


def format_sonarr(data: dict[str, Any]) -> str:
    series = nested(data, "series")
    episode = nested(data, "episode")
    title = first_non_empty(pick(series, "title"), pick(data, "series.title"), "Unknown series")
    season = first_non_empty(pick(episode, "seasonNumber"), pick(data, "seasonNumber"))
    episode_num = first_non_empty(pick(episode, "episodeNumber"), pick(data, "episodeNumber"))
    ep_title = first_non_empty(pick(episode, "title"), pick(data, "episode.title"), "Unknown episode")
    code = f"S{int(season):02d}E{int(episode_num):02d}" if season.isdigit() and episode_num.isdigit() else ""

    lines = ["<b>New episode imported</b>"]
    lines.append(html.escape(" - ".join(x for x in [title, code, ep_title] if x)))

    q = quality(data)
    if q:
        lines.append(f"Quality: {html.escape(q)}")
    rg = release_group(data)
    if rg:
        lines.append(f"Release group: {html.escape(rg)}")

    imdb_id = first_non_empty(pick(series, "imdbId"), pick(data, "series.imdbId"))
    episode_tvdb = first_non_empty(pick(episode, "tvdbId"), pick(data, "episode.tvdbId"))
    series_tvdb = first_non_empty(pick(series, "tvdbId"), pick(data, "series.tvdbId"))
    links = []
    if imdb_id:
        links.append(link_line("IMDB", imdb_url(imdb_id)))
    if episode_tvdb:
        links.append(link_line("TVDB episode", tvdb_url(episode_tvdb, "episode")))
    elif series_tvdb:
        links.append(link_line("TVDB series", tvdb_url(series_tvdb, "series")))
    if links:
        lines.append("Links: " + " | ".join(links))

    if JELLYFIN_NOTE:
        lines.append(html.escape(JELLYFIN_NOTE))
    return "\n".join(lines)


def format_radarr(data: dict[str, Any]) -> str:
    movie = nested(data, "movie")
    title = first_non_empty(pick(movie, "title"), pick(data, "movie.title"), "Unknown movie")
    year = first_non_empty(pick(movie, "year"), pick(data, "movie.year"))
    heading = f"{title} ({year})" if year else title

    lines = ["<b>New movie imported</b>", html.escape(heading)]
    q = quality(data)
    if q:
        lines.append(f"Quality: {html.escape(q)}")
    rg = release_group(data)
    if rg:
        lines.append(f"Release group: {html.escape(rg)}")

    imdb_id = first_non_empty(pick(movie, "imdbId"), pick(data, "movie.imdbId"))
    tmdb_id = first_non_empty(pick(movie, "tmdbId"), pick(data, "movie.tmdbId"))
    links = []
    if imdb_id:
        links.append(link_line("IMDB", imdb_url(imdb_id)))
    if tmdb_id:
        links.append(link_line("TMDB", f"https://www.themoviedb.org/movie/{urllib.parse.quote(tmdb_id)}"))
    if links:
        lines.append("Links: " + " | ".join(links))

    if JELLYFIN_NOTE:
        lines.append(html.escape(JELLYFIN_NOTE))
    return "\n".join(lines)


def telegram_send(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8", "replace")
        if resp.status >= 300:
            raise RuntimeError(f"Telegram returned HTTP {resp.status}: {body}")


class Handler(BaseHTTPRequestHandler):
    server_version = "media-import-notifier/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        msg = fmt % args
        if WEBHOOK_TOKEN:
            msg = msg.replace(WEBHOOK_TOKEN, "[redacted]")
        print(f"{self.address_string()} - {msg}", file=sys.stderr, flush=True)

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self.send_json(200, {"ok": True})
            return
        self.send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        service = parsed.path.strip("/").split("/")[-1].lower()
        if service not in {"sonarr", "radarr"}:
            self.send_json(404, {"ok": False, "error": "use /webhook/sonarr or /webhook/radarr"})
            return

        params = urllib.parse.parse_qs(parsed.query)
        if WEBHOOK_TOKEN and params.get("token", [""])[0] != WEBHOOK_TOKEN:
            self.send_json(401, {"ok": False, "error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            event = pick(data, "eventType", default="")
            if event and event not in IMPORT_EVENTS:
                self.send_json(202, {"ok": True, "ignored": event})
                return
            message = format_sonarr(data) if service == "sonarr" else format_radarr(data)
            telegram_send(message)
            self.send_json(200, {"ok": True})
        except Exception as exc:
            print(f"error handling {service} webhook: {exc}", file=sys.stderr, flush=True)
            self.send_json(500, {"ok": False, "error": str(exc)})


if __name__ == "__main__":
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"media-import-notifier listening on {HOST}:{PORT}", flush=True)
    httpd.serve_forever()
