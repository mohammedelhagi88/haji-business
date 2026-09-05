"""Models for image input."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ImageInput:
    """A user-supplied image reference.

    The binary image is handled by the mobile/API layer; this model keeps the
    orchestration layer independent from a particular storage provider.
    """

    image_id: str
    mime_type: str
    source: str = "upload"
    caption: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not self.image_id.strip():
            raise ValueError("image_id is required")
        if not self.mime_type.startswith("image/"):
            raise ValueError("mime_type must be an image MIME type")
