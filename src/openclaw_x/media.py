"""Media upload via X API v1.1 chunked upload (httpx, no tweepy)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx

from .auth import Credentials, generate_oauth_header

UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"

# Supported MIME types and their categories
MIME_TYPES: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
}

MEDIA_CATEGORIES: dict[str, str] = {
    "image/jpeg": "tweet_image",
    "image/png": "tweet_image",
    "image/webp": "tweet_image",
    "image/gif": "tweet_gif",
    "video/mp4": "tweet_video",
}

# Max file sizes (bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_GIF_SIZE = 15 * 1024 * 1024  # 15 MB
MAX_VIDEO_SIZE = 512 * 1024 * 1024  # 512 MB
CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB per chunk


class MediaUploadError(Exception):
    """Raised when media upload fails."""


class MediaUploader:
    """Chunked media upload via X API v1.1 upload endpoint."""

    def __init__(self, creds: Credentials) -> None:
        self.creds = creds
        self._http = httpx.Client(timeout=60.0)

    def close(self) -> None:
        self._http.close()

    def upload(self, file_path: str | Path) -> str:
        """Upload a media file and return the media_id string.

        Supports JPG, PNG, WEBP, GIF, and MP4.
        Uses chunked upload (INIT -> APPEND -> FINALIZE -> STATUS polling).
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise MediaUploadError(f"File not found: {path}")

        suffix = path.suffix.lower()
        mime_type = MIME_TYPES.get(suffix)
        if not mime_type:
            supported = ", ".join(MIME_TYPES.keys())
            raise MediaUploadError(f"Unsupported file type: {suffix}. Supported: {supported}")

        file_size = path.stat().st_size
        self._validate_size(mime_type, file_size)

        media_category = MEDIA_CATEGORIES[mime_type]

        # Step 1: INIT
        media_id = self._init(file_size, mime_type, media_category)

        # Step 2: APPEND (chunked)
        self._append(media_id, path, file_size)

        # Step 3: FINALIZE
        processing_info = self._finalize(media_id)

        # Step 4: STATUS (poll if async processing, e.g. video)
        if processing_info:
            self._poll_status(media_id, processing_info)

        return media_id

    def _validate_size(self, mime_type: str, file_size: int) -> None:
        if mime_type == "video/mp4":
            max_size = MAX_VIDEO_SIZE
        elif mime_type == "image/gif":
            max_size = MAX_GIF_SIZE
        else:
            max_size = MAX_IMAGE_SIZE

        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise MediaUploadError(f"File too large: {actual_mb:.1f} MB (max {max_mb:.0f} MB for {mime_type})")

    def _oauth_post(self, params: dict[str, str], data: dict[str, Any] | None = None, files: Any = None) -> dict:
        """POST to upload endpoint with OAuth 1.0a signing."""
        # Build URL with query params for OAuth signature
        auth_header = generate_oauth_header("POST", UPLOAD_URL, self.creds, params)
        headers = {"Authorization": auth_header}

        resp = self._http.post(UPLOAD_URL, params=params, data=data, files=files, headers=headers)

        if not resp.is_success:
            raise MediaUploadError(f"Upload failed (HTTP {resp.status_code}): {resp.text[:500]}")

        if resp.content:
            return resp.json()
        return {}

    def _init(self, total_bytes: int, media_type: str, media_category: str) -> str:
        """INIT command: allocate upload and get media_id."""
        params = {
            "command": "INIT",
            "total_bytes": str(total_bytes),
            "media_type": media_type,
            "media_category": media_category,
        }
        result = self._oauth_post(params)
        return str(result["media_id_string"])

    def _append(self, media_id: str, path: Path, file_size: int) -> None:
        """APPEND command: upload file in chunks."""
        segment_index = 0
        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                params = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": str(segment_index),
                }
                auth_header = generate_oauth_header("POST", UPLOAD_URL, self.creds, params)
                headers = {"Authorization": auth_header}

                resp = self._http.post(
                    UPLOAD_URL,
                    params=params,
                    files={"media_data": ("chunk", chunk, "application/octet-stream")},
                    headers=headers,
                )
                if not resp.is_success:
                    raise MediaUploadError(
                        f"APPEND segment {segment_index} failed (HTTP {resp.status_code}): {resp.text[:500]}"
                    )
                segment_index += 1

    def _finalize(self, media_id: str) -> dict | None:
        """FINALIZE command: complete upload and check processing state."""
        params = {
            "command": "FINALIZE",
            "media_id": media_id,
        }
        result = self._oauth_post(params)
        return result.get("processing_info")

    def _poll_status(self, media_id: str, processing_info: dict) -> None:
        """Poll STATUS until processing completes (for video/gif)."""
        while processing_info:
            state = processing_info.get("state")
            if state == "succeeded":
                return
            if state == "failed":
                error = processing_info.get("error", {})
                msg = error.get("message", "Unknown processing error")
                raise MediaUploadError(f"Media processing failed: {msg}")

            check_after = processing_info.get("check_after_secs", 5)
            time.sleep(check_after)

            params = {
                "command": "STATUS",
                "media_id": media_id,
            }
            auth_header = generate_oauth_header("GET", UPLOAD_URL, self.creds, params)
            headers = {"Authorization": auth_header}
            resp = self._http.get(UPLOAD_URL, params=params, headers=headers)

            if not resp.is_success:
                raise MediaUploadError(f"STATUS check failed (HTTP {resp.status_code}): {resp.text[:500]}")

            result = resp.json()
            processing_info = result.get("processing_info")
