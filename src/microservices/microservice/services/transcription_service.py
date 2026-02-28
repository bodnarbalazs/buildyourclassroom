from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import structlog
from openai import AzureOpenAI
from pydub import AudioSegment
from pydub.silence import detect_silence
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".mpga", ".m4a", ".wav"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mpeg"}
SUPPORTED_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS | {".txt"}

MAX_CHUNK_BYTES = 24 * 1024 * 1024  # 24 MB to stay safely under the 25 MB limit
CONTEXT_CHARS = 200


class TranscriptionError(Exception):
    pass


_REQUIRED_ENV_VARS = [
    "AZURE_OPENAI_WHISPER_ENDPOINT",
    "AZURE_OPENAI_WHISPER_API_KEY",
    "AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME",
]


class TranscriptionService:
    def __init__(self) -> None:
        missing = [v for v in _REQUIRED_ENV_VARS if v not in os.environ]
        if missing:
            raise TranscriptionError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        # Whisper SDK calls are synchronous — we wrap them with asyncio.to_thread
        self._client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_WHISPER_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_WHISPER_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_WHISPER_API_VERSION", "2024-10-21"),
        )
        self._deployment = os.environ["AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME"]

    async def transcribe_file(self, file_path: Path) -> TranscriptionResult:
        ext = file_path.suffix.lower()
        if ext == ".txt":
            text = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
            if not text.strip():
                raise TranscriptionError("Transcript file is empty")
            return TranscriptionResult(text=text.strip(), segments=[])

        if ext not in SUPPORTED_EXTENSIONS:
            raise TranscriptionError(f"Unsupported file format: {ext}")

        audio_path = file_path
        tmp_audio: Path | None = None
        try:
            if ext in SUPPORTED_VIDEO_EXTENSIONS:
                log = logger.bind(source=file_path.name)
                log.info("extracting_audio_from_video")
                tmp_audio = await self._extract_audio(file_path)
                audio_path = tmp_audio

            file_size = audio_path.stat().st_size
            if file_size > MAX_CHUNK_BYTES:
                return await self._transcribe_chunked(audio_path)
            return await self._transcribe_single(audio_path)
        finally:
            if tmp_audio and tmp_audio.exists():
                tmp_audio.unlink()

    async def _extract_audio(self, video_path: Path) -> Path:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        output_path = Path(tmp.name)
        try:
            audio = await asyncio.to_thread(AudioSegment.from_file, str(video_path))
            await asyncio.to_thread(
                audio.export, str(output_path), format="mp3", parameters=["-q:a", "2"]
            )
        except Exception as exc:
            output_path.unlink(missing_ok=True)
            raise TranscriptionError(f"Failed to extract audio: {exc}") from exc
        return output_path

    async def _transcribe_single(self, audio_path: Path) -> TranscriptionResult:
        log = logger.bind(file=audio_path.name)
        log.info("transcribing_single_file")
        result = await asyncio.to_thread(self._call_whisper, audio_path, prompt=None)
        return result

    async def _transcribe_chunked(self, audio_path: Path) -> TranscriptionResult:
        log = logger.bind(file=audio_path.name)
        log.info("transcribing_chunked", reason="file exceeds 24MB")

        audio = await asyncio.to_thread(AudioSegment.from_file, str(audio_path))
        chunk_paths = await asyncio.to_thread(self._split_audio, audio, audio_path)

        log.info("chunks_created", count=len(chunk_paths))

        all_text: list[str] = []
        all_segments: list[dict] = []
        prev_context: str | None = None

        try:
            for i, chunk_path in enumerate(chunk_paths):
                log.info("transcribing_chunk", chunk=i + 1, total=len(chunk_paths))
                result = await asyncio.to_thread(
                    self._call_whisper, chunk_path, prompt=prev_context
                )
                all_text.append(result.text)
                all_segments.extend(result.segments)
                prev_context = result.text[-CONTEXT_CHARS:] if result.text else None
        finally:
            for p in chunk_paths:
                p.unlink(missing_ok=True)

        full_text = " ".join(all_text)
        return TranscriptionResult(text=full_text, segments=all_segments)

    def _split_audio(self, audio: AudioSegment, source_path: Path) -> list[Path]:
        duration_ms = len(audio)
        if duration_ms == 0:
            raise TranscriptionError("Audio file has zero duration")

        # Estimate bitrate and calculate chunk duration
        file_size = source_path.stat().st_size
        bytes_per_ms = file_size / duration_ms
        chunk_duration_ms = int(MAX_CHUNK_BYTES / bytes_per_ms)

        # Try to split at silence boundaries
        silence_ranges = detect_silence(audio, min_silence_len=500, silence_thresh=-40)
        silence_points = {(start + end) // 2 for start, end in silence_ranges}

        chunks: list[Path] = []
        pos = 0
        while pos < duration_ms:
            end = min(pos + chunk_duration_ms, duration_ms)
            if end < duration_ms:
                # Look for a silence point near the intended split
                best = None
                for sp in silence_points:
                    if pos + chunk_duration_ms * 0.8 <= sp <= end:
                        best = sp
                        break
                if best is not None:
                    end = best

            chunk = audio[pos:end]
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()
            chunk_path = Path(tmp.name)
            chunk.export(str(chunk_path), format="mp3", parameters=["-q:a", "2"])
            chunks.append(chunk_path)
            pos = end

        return chunks

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _call_whisper(self, audio_path: Path, prompt: str | None) -> TranscriptionResult:
        with open(audio_path, "rb") as f:
            kwargs: dict = {
                "model": self._deployment,
                "file": f,
                "response_format": "verbose_json",
            }
            if prompt:
                kwargs["prompt"] = prompt
            response = self._client.audio.transcriptions.create(**kwargs)

        text = response.text or ""
        segments: list[dict] = []
        if hasattr(response, "segments") and response.segments:
            segments = [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in response.segments
                if hasattr(s, "start")
            ]
        return TranscriptionResult(text=text, segments=segments)


class TranscriptionResult:
    __slots__ = ("text", "segments")

    def __init__(self, text: str, segments: list[dict]) -> None:
        self.text = text
        self.segments = segments
