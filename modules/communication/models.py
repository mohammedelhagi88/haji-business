"""Domain models for communication requests.

The module describes intended actions; adapters can later connect to phone/SMS/social
providers. Sending is never implicit.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CommunicationChannel(str, Enum):
    CALL = "call"
    SMS = "sms"
    SOCIAL = "social"


class CommunicationAction(str, Enum):
    PREPARE = "prepare"
    SEND = "send"
    CALL = "call"


@dataclass
class CommunicationRequest:
    recipient: str
    channel: CommunicationChannel
    action: CommunicationAction
    message: Optional[str] = None
    provider: Optional[str] = None
    approved: bool = False
    metadata: dict = field(default_factory=dict)

    @property
    def requires_confirmation(self) -> bool:
        """Whether an external communication must be explicitly approved."""
        return self.action in {CommunicationAction.SEND, CommunicationAction.CALL}
