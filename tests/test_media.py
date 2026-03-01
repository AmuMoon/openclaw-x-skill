"""Tests for openclaw_x.media."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from openclaw_x.media import (
    MIME_TYPES,
    MediaUploader,
    MediaUploadError,
)


@pytest.fixture
def uploader(creds):
    up = MediaUploader(creds)
    yield up
    up.close()


@pytest.fixture
def tmp_image(tmp_path):
    """Create a tiny valid-ish JPEG file."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    return img


@pytest.fixture
def tmp_video(tmp_path):
    """Create a small fake MP4 file."""
    vid = tmp_path / "test.mp4"
    vid.write_bytes(b"\x00\x00\x00\x1c\x66\x74\x79\x70" + b"\x00" * 1000)
    return vid


class TestMediaUploader:
    def test_file_not_found(self, uploader):
        with pytest.raises(MediaUploadError, match="File not found"):
            uploader.upload("/nonexistent/file.jpg")

    def test_unsupported_format(self, uploader, tmp_path):
        bad = tmp_path / "test.bmp"
        bad.write_bytes(b"\x00" * 100)
        with pytest.raises(MediaUploadError, match="Unsupported file type"):
            uploader.upload(bad)

    def test_file_too_large(self, uploader, tmp_path):
        big = tmp_path / "big.jpg"
        big.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * (6 * 1024 * 1024))
        with pytest.raises(MediaUploadError, match="File too large"):
            uploader.upload(big)

    def test_mime_types_cover_expected_formats(self):
        assert ".jpg" in MIME_TYPES
        assert ".jpeg" in MIME_TYPES
        assert ".png" in MIME_TYPES
        assert ".gif" in MIME_TYPES
        assert ".mp4" in MIME_TYPES
        assert ".webp" in MIME_TYPES

    def test_upload_success_mocked(self, uploader, tmp_image):
        """Test full upload flow with mocked HTTP."""
        mock_resp_init = MagicMock()
        mock_resp_init.is_success = True
        mock_resp_init.content = b'{"media_id_string": "12345"}'
        mock_resp_init.json.return_value = {"media_id_string": "12345"}

        mock_resp_append = MagicMock()
        mock_resp_append.is_success = True

        mock_resp_finalize = MagicMock()
        mock_resp_finalize.is_success = True
        mock_resp_finalize.content = b'{"media_id_string": "12345"}'
        mock_resp_finalize.json.return_value = {"media_id_string": "12345"}

        with patch.object(uploader._http, "post") as mock_post:
            mock_post.side_effect = [mock_resp_init, mock_resp_append, mock_resp_finalize]
            media_id = uploader.upload(tmp_image)
            assert media_id == "12345"
            assert mock_post.call_count == 3

    def test_upload_video_polls_status(self, uploader, tmp_video):
        """Test that video upload polls processing status."""
        mock_resp_init = MagicMock()
        mock_resp_init.is_success = True
        mock_resp_init.content = b'{"media_id_string": "99999"}'
        mock_resp_init.json.return_value = {"media_id_string": "99999"}

        mock_resp_append = MagicMock()
        mock_resp_append.is_success = True

        mock_resp_finalize = MagicMock()
        mock_resp_finalize.is_success = True
        mock_resp_finalize.content = b'ok'
        mock_resp_finalize.json.return_value = {
            "media_id_string": "99999",
            "processing_info": {"state": "pending", "check_after_secs": 0},
        }

        mock_resp_status = MagicMock()
        mock_resp_status.is_success = True
        mock_resp_status.json.return_value = {
            "processing_info": {"state": "succeeded"},
        }

        with (
            patch.object(uploader._http, "post") as mock_post,
            patch.object(uploader._http, "get") as mock_get,
        ):
            mock_post.side_effect = [mock_resp_init, mock_resp_append, mock_resp_finalize]
            mock_get.return_value = mock_resp_status
            media_id = uploader.upload(tmp_video)
            assert media_id == "99999"
            mock_get.assert_called_once()
