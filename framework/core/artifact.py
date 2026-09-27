from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ShellArtifact:
    plan_id: str
    script: str
    manifest: Mapping[str, Any]
