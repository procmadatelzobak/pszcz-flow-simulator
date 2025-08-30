"""Basic smoke test to ensure required dependencies are present."""


def test_websockets_importable() -> None:
    """`websockets` should be importable once installed via requirements."""
    import websockets  # noqa: F401
