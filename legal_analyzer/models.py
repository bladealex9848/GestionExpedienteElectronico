from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PageTrace:
    document: str
    page: int
    text: str
    extraction_method: str
    ocr_confidence: float | None = None
    useful_characters: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrderRecord:
    order_id: int
    text: str
    source_document: str
    source_page: int
    responsible: str
    deadline: str
    conduct: str
    keywords: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceRecord:
    document: str
    page: int
    fragment: str
    similarity: float
    compliance_signal: float
    timeliness_signal: float
    responsibility_signal: float
    integrity_signal: float
    ocr_quality: float
    trace_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceAssessment:
    order_id: int
    conduct_score: float
    responsible_score: float
    evidence_score: float
    timeliness_score: float
    integrity_score: float
    ocr_quality_score: float
    total_score: float
    automatic_status: str
    reasoning: str
    best_evidence: EvidenceRecord | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.best_evidence is not None:
            data["best_evidence"] = self.best_evidence.to_dict()
        return data
