try:
    import importlib.metadata

    __version__ = importlib.metadata.version("phototagging")

except Exception:
    __version__ = "0.0.0"
