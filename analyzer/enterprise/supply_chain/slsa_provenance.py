"""Compatibility SLSA provenance generator."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class SLSAProvenanceGenerator:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", ".artifacts/supply_chain"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_build_metadata(self, project_root: str) -> Dict[str, Any]:
        return {
            "build_id": str(uuid.uuid4()),
            "project_root": str(project_root),
            "started_on": datetime.now(timezone.utc).isoformat(),
            "builder": "local-test-builder",
        }

    def generate_provenance(
        self, artifacts: List[Dict[str, Any]], build_metadata: Dict[str, Any]
    ) -> str:
        provenance = {
            "_type": "https://in-toto.io/Statement/v0.1",
            "predicateType": "https://slsa.dev/provenance/v1",
            "subject": [
                {"name": artifact["name"], "digest": {"sha256": artifact.get("sha256", "")}}
                for artifact in artifacts
            ],
            "predicate": {
                "buildDefinition": {
                    "buildType": "https://connascence.local/build/test",
                    "externalParameters": build_metadata,
                    "resolvedDependencies": [],
                },
                "runDetails": {"builder": {"id": "local-test-builder"}},
            },
        }
        output = self.output_dir / "slsa-provenance.json"
        output.write_text(json.dumps(provenance, indent=2))
        return str(output)
