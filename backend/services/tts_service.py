import httpx
import hashlib
import time

from typing import Optional, Dict, Tuple
from pathlib import Path
from elevenlabs.client import ElevenLabs
from config import settings


class TextToSpeechService:
    def __init__(self) -> None:
        self.api_key = settings.ELEVENLABS_API_KEY
        self.default_voice_id = settings.ELEVENLABS_VOICE_ID
        self.model_id = settings.ELEVENLABS_MODEL_ID
        self.available = bool(self.api_key)
        self.client = ElevenLabs(api_key=self.api_key) if self.available else None
        self.cache_enabled = settings.TTS_CACHE_ENABLED
        self.cache_ttl_seconds = max(0, settings.TTS_CACHE_TTL_SECONDS)
        self.cache_max_files = max(0, settings.TTS_CACHE_MAX_FILES)
        self.cache_dir = Path(settings.AUDIO_UPLOAD_DIR) / "tts_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_writes = 0
        self.cache_evictions = 0
        self.provider_status_ttl_seconds = 60
        self._provider_status_checked_at = 0.0
        self._provider_ready = False
        self._provider_reason: Optional[str] = None

    async def check_provider_health(self, force: bool = False) -> Tuple[bool, Optional[str]]:
        if not self.available:
            self._provider_ready = False
            self._provider_reason = "api_key_missing"
            self._provider_status_checked_at = time.time()
            return self._provider_ready, self._provider_reason

        now = time.time()
        if (
            not force
            and self._provider_status_checked_at > 0
            and (now - self._provider_status_checked_at) < self.provider_status_ttl_seconds
        ):
            return self._provider_ready, self._provider_reason

        headers = {
            "xi-api-key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get("https://api.elevenlabs.io/v1/user", headers=headers)

            if response.status_code == 200:
                self._provider_ready = True
                self._provider_reason = None
            elif response.status_code == 401:
                self._provider_ready = False
                reason = "invalid_api_key"
                try:
                    payload = response.json() if response.content else {}
                    detail = payload.get("detail") if isinstance(payload, dict) else None
                    if isinstance(detail, dict):
                        status_code = str(detail.get("status") or "").strip().lower()
                        message = str(detail.get("message") or "").strip().lower()
                        if status_code == "missing_permissions":
                            if "user_read" in message:
                                reason = "missing_permission_user_read"
                            else:
                                reason = "missing_permissions"
                except Exception:
                    pass
                self._provider_reason = reason
            elif response.status_code == 429:
                self._provider_ready = False
                self._provider_reason = "rate_limited"
            else:
                self._provider_ready = False
                self._provider_reason = f"provider_http_{response.status_code}"
        except httpx.TimeoutException:
            self._provider_ready = False
            self._provider_reason = "provider_timeout"
        except Exception:
            self._provider_ready = False
            self._provider_reason = "provider_unreachable"

        self._provider_status_checked_at = time.time()
        return self._provider_ready, self._provider_reason

    def apply_runtime_config(self, runtime_config: Optional[Dict] = None) -> None:
        config = runtime_config or {}
        self.default_voice_id = config.get("tts_default_voice_id") or settings.ELEVENLABS_VOICE_ID
        self.model_id = config.get("tts_model_id") or settings.ELEVENLABS_MODEL_ID
        self.cache_enabled = bool(config.get("tts_cache_enabled", settings.TTS_CACHE_ENABLED))
        self.cache_ttl_seconds = max(0, int(config.get("tts_cache_ttl_seconds", settings.TTS_CACHE_TTL_SECONDS)))
        self.cache_max_files = max(0, int(config.get("tts_cache_max_files", settings.TTS_CACHE_MAX_FILES)))

    def clear_cache(self) -> int:
        removed = 0
        for file_path in self._cache_files():
            try:
                file_path.unlink(missing_ok=True)
                removed += 1
            except Exception:
                continue
        return removed

    def _cache_files(self):
        return [path for path in self.cache_dir.glob("*.mp3") if path.is_file()]

    def _cleanup_cache(self) -> None:
        if not self.cache_enabled:
            return 0

        try:
            files = self._cache_files()
        except Exception:
            return 0

        now = time.time()
        active_files = []
        removed_count = 0
        for file_path in files:
            try:
                modified = file_path.stat().st_mtime
                if self.cache_ttl_seconds > 0 and (now - modified) > self.cache_ttl_seconds:
                    file_path.unlink(missing_ok=True)
                    removed_count += 1
                else:
                    active_files.append(file_path)
            except Exception:
                continue

        if self.cache_max_files > 0 and len(active_files) > self.cache_max_files:
            active_files.sort(key=lambda p: p.stat().st_mtime)
            remove_count = len(active_files) - self.cache_max_files
            for file_path in active_files[:remove_count]:
                try:
                    file_path.unlink(missing_ok=True)
                    removed_count += 1
                except Exception:
                    continue

        if removed_count > 0:
            self.cache_evictions += removed_count

        return removed_count

    def _build_cache_key(
        self,
        text: str,
        voice_id: str,
        stability: Optional[float],
        similarity_boost: Optional[float],
    ) -> str:
        payload = "|".join(
            [
                self.model_id or "",
                voice_id or "",
                "" if stability is None else f"{stability:.3f}",
                "" if similarity_boost is None else f"{similarity_boost:.3f}",
                text,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def list_voices(self):
        if not self.available:
            raise RuntimeError("ElevenLabs API key is not configured.")

        headers = {
            "xi-api-key": self.api_key,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get("https://api.elevenlabs.io/v1/voices", headers=headers)
            response.raise_for_status()

        data = response.json()
        voices = data.get("voices", []) if isinstance(data, dict) else []
        return [
            {
                "voice_id": voice.get("voice_id"),
                "name": voice.get("name"),
                "category": voice.get("category"),
                "description": voice.get("description"),
                "labels": voice.get("labels") or {},
            }
            for voice in voices
            if voice.get("voice_id")
        ]

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
    ):
        if not self.available:
            raise RuntimeError("ElevenLabs API key is not configured.")

        resolved_voice_id = voice_id or self.default_voice_id
        if not resolved_voice_id:
            raise RuntimeError("ElevenLabs voice id is not configured.")

        cache_key = self._build_cache_key(
            text=text,
            voice_id=resolved_voice_id,
            stability=stability,
            similarity_boost=similarity_boost,
        )
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        self._cleanup_cache()
        if self.cache_enabled and cache_file.exists() and cache_file.stat().st_size > 0:
            self.cache_hits += 1
            cache_file.touch(exist_ok=True)
            return cache_file.read_bytes(), "audio/mpeg"
        self.cache_misses += 1

        voice_settings = None
        if stability is not None or similarity_boost is not None:
            voice_settings = {
                "stability": stability if stability is not None else settings.ELEVENLABS_STABILITY,
                "similarity_boost": similarity_boost if similarity_boost is not None else settings.ELEVENLABS_SIMILARITY,
            }

        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=resolved_voice_id,
            model_id=self.model_id,
            output_format="mp3_44100_128",
            optimize_streaming_latency=0,
            voice_settings=voice_settings,
        )

        if isinstance(audio, bytes):
            audio_bytes = audio
        else:
            audio_bytes = b"".join(chunk for chunk in audio)

        if self.cache_enabled and audio_bytes:
            cache_file.write_bytes(audio_bytes)
            self.cache_writes += 1
            self._cleanup_cache()

        return audio_bytes, "audio/mpeg"

    def get_cache_stats(self) -> Dict:
        try:
            files = self._cache_files()
            file_count = len(files)
            size_bytes = sum(path.stat().st_size for path in files)
        except Exception:
            file_count = 0
            size_bytes = 0

        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests) if total_requests > 0 else 0.0

        return {
            "enabled": self.cache_enabled,
            "ttl_seconds": self.cache_ttl_seconds,
            "max_files": self.cache_max_files,
            "file_count": file_count,
            "size_bytes": size_bytes,
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "writes": self.cache_writes,
            "evictions": self.cache_evictions,
            "hit_rate": hit_rate,
        }


tts_service = TextToSpeechService()
