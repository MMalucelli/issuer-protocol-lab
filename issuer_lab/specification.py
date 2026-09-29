from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from typing import Any

SCHEMA_VERSION = 2

@dataclass(frozen=True)
class LabSpecification:
    name: str
    data: dict[str, Any]
    derived_defs: list[dict[str, Any]]
    memory: dict[str, Any]
    capacity: dict[str, Any]
    intrawindow: dict[str, Any]
    actions: list[dict[str, Any]]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LabSpecification':
        version = int(data.get('schema_version', 0))
        if version != SCHEMA_VERSION:
            raise ValueError(f'versão de especificação não suportada: {version}')
        return cls(
            name=str(data.get('name', 'Imported specification')),
            data=dict(data.get('data', {})),
            derived_defs=list(data.get('derived_defs', [])),
            memory=dict(data.get('memory', {})),
            capacity=dict(data.get('capacity', {})),
            intrawindow=dict(data.get('intrawindow', {})),
            actions=list(data.get('actions', [])),
            schema_version=version,
        )

    @classmethod
    def from_json(cls, raw: str | bytes) -> 'LabSpecification':
        if isinstance(raw, bytes): raw = raw.decode('utf-8')
        data = json.loads(raw)
        if not isinstance(data, dict): raise ValueError('a especificação deve ser um objeto JSON')
        return cls.from_dict(data)
