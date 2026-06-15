"""Smoke tests proving the package layout and toolchain are wired correctly.

Real behavior tests arrive with their features (FastAPI health check in PR-004, etc.).
"""

import jobhunter


def test_package_imports() -> None:
    assert jobhunter.__version__ == "0.0.0"
