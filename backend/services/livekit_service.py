import re
import uuid
from typing import Optional, Tuple
from datetime import timedelta

from config import settings

try:
    from livekit import api as livekit_api
except ImportError:  # pragma: no cover
    livekit_api = None


class LiveKitService:
    def _sanitize_room_name(self, raw_name: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", raw_name or "")
        cleaned = re.sub(r"-+", "-", cleaned).strip("-")
        return cleaned[:128] or f"{settings.LIVEKIT_ROOM_PREFIX}-room"

    def is_enabled(self) -> bool:
        return bool(settings.VOICE_AGENT_RUNTIME_ENABLED)

    def is_configured(self) -> bool:
        return bool(
            settings.LIVEKIT_URL
            and settings.LIVEKIT_API_KEY
            and settings.LIVEKIT_API_SECRET
        )

    def get_runtime_status(self) -> dict:
        return {
            "enabled": self.is_enabled(),
            "provider": settings.VOICE_PROVIDER,
            "configured": self.is_configured(),
            "livekit_url": settings.LIVEKIT_URL or None,
        }

    def issue_session_token(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        room_name: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Tuple[str, str, str, int]:
        if not self.is_enabled():
            raise RuntimeError("Voice agent runtime is disabled")
        if settings.VOICE_PROVIDER != "livekit":
            raise RuntimeError(f"Unsupported voice provider: {settings.VOICE_PROVIDER}")
        if not self.is_configured():
            raise RuntimeError("LiveKit is not fully configured")
        if livekit_api is None:
            raise RuntimeError("livekit-api dependency is not installed")

        room_seed = room_name or f"{settings.LIVEKIT_ROOM_PREFIX}-{session_id}"
        resolved_room_name = self._sanitize_room_name(room_seed)
        identity = user_id or f"anon-{uuid.uuid4().hex[:8]}"
        token_name = display_name or identity

        grants = livekit_api.VideoGrants(
            room_join=True,
            room=resolved_room_name,
            can_publish=True,
            can_subscribe=True,
        )

        access_token = (
            livekit_api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(identity)
            .with_name(token_name)
            .with_grants(grants)
            .with_ttl(timedelta(seconds=settings.LIVEKIT_TOKEN_TTL_SECONDS))
        )
        jwt_token = access_token.to_jwt()

        return jwt_token, resolved_room_name, identity, settings.LIVEKIT_TOKEN_TTL_SECONDS


livekit_service = LiveKitService()
