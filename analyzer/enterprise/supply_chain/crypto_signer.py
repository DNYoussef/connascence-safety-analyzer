"""Cryptographic signing compatibility layer."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List


class CryptographicSigner:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def _is_cosign_available(self) -> bool:
        return False

    def sign_artifacts(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        signed = []
        for artifact in artifacts:
            path = Path(artifact["path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""
            signed.append(
                {
                    "artifact_path": str(path),
                    "signing_method": "sha256-local",
                    "sha256": digest,
                }
            )
        return {
            "signing_timestamp": "",
            "artifacts": signed,
            "signatures_created": len(signed),
            "errors": [],
        }
