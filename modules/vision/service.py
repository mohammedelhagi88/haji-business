"""Vision orchestration layer.

This layer accepts image inputs and prepares them for a vision-capable model.
It intentionally does not hard-code a provider; the mobile/API layer can attach
an implementation later.
"""

from dataclasses import dataclass
from typing import Any, Callable

from .models import ImageInput


@dataclass(frozen=True)
class VisionResult:
    status: str
    image: ImageInput
    result: Any = None
    detail: str = ""


class VisionService:
    def __init__(self, analyzer: Callable[[ImageInput], Any] | None = None) -> None:
        self._analyzer = analyzer

    def receive(self, image: ImageInput) -> VisionResult:
        image.validate()
        if self._analyzer is None:
            return VisionResult(
                "received",
                image,
                detail="الصورة وصلت وجاهزة للتحليل عبر مزود الرؤية.",
            )
        return VisionResult("analyzed", image, self._analyzer(image))
