from pathlib import Path


def test_requirements_pins_hf_hub_below_1():
    content = Path("requirements.txt").read_text(encoding="utf-8")
    assert "huggingface_hub==0.34.4" in content or "huggingface_hub<1.0" in content


def test_requirements_include_openai_sdk():
    content = Path("requirements.txt").read_text(encoding="utf-8")
    assert "openai" in content
