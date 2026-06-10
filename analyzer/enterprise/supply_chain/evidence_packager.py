"""Evidence packaging helpers."""

from __future__ import annotations

import hashlib
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class EvidencePackager:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def _calculate_multiple_hashes(self, file_path: str) -> Dict[str, str]:
        data = Path(file_path).read_bytes()
        hashes = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "sha512": hashlib.sha512(data).hexdigest(),
        }
        if self.config.get("allow_legacy_hashes", False):
            hashes["sha1"] = hashlib.sha1(data).hexdigest()  # nosec B324 - explicit legacy-hash opt-in
        return hashes

    def create_evidence_package(
        self, project_root: str, artifacts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        output_dir = Path(self.config.get("output_dir", Path(project_root) / ".artifacts" / "supply_chain"))
        output_dir.mkdir(parents=True, exist_ok=True)
        package_path = output_dir / "evidence.zip"
        files_included = 0
        with zipfile.ZipFile(package_path, "w") as archive:
            for artifact in artifacts:
                path = Path(artifact["path"])
                if path.exists():
                    archive.write(path, arcname=path.name)
                    files_included += 1
        return {
            "package_id": str(uuid.uuid4()),
            "created": datetime.now(timezone.utc).isoformat(),
            "evidence_types": [artifact.get("type", "artifact") for artifact in artifacts],
            "package_path": str(package_path),
            "files_included": files_included,
            "package_size": package_path.stat().st_size if package_path.exists() else 0,
        }
