import pytest

from modules.vision import ImageInput, VisionService


def test_image_is_received_without_provider():
    image = ImageInput("img-1", "image/jpeg", caption="test")
    result = VisionService().receive(image)
    assert result.status == "received"
    assert result.image.image_id == "img-1"


def test_vision_provider_can_analyze_image():
    image = ImageInput("chart-1", "image/png")
    result = VisionService(lambda item: {"kind": "chart", "id": item.image_id}).receive(image)
    assert result.status == "analyzed"
    assert result.result["kind"] == "chart"


def test_non_image_is_rejected():
    image = ImageInput("file-1", "application/pdf")
    with pytest.raises(ValueError):
        VisionService().receive(image)
