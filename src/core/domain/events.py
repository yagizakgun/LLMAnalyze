from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from .models import Signal, AnalysisResult, Alert

@dataclass
class DomainEvent:
    event_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class SignalGenerated(DomainEvent):
    signal: Signal

@dataclass
class AnalysisCompleted(DomainEvent):
    analysis: AnalysisResult

@dataclass
class AlertTriggered(DomainEvent):
    alert: Alert
    current_value: float
    message: str
