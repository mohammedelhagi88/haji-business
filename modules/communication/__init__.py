"""Communication module for contacts, calls, messages, and social messaging."""

from .models import CommunicationAction, CommunicationChannel, CommunicationRequest
from .service import CommunicationService

__all__ = [
    "CommunicationAction",
    "CommunicationChannel",
    "CommunicationRequest",
    "CommunicationService",
]
