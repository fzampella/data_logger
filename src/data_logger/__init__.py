import os


DEFAULT_PORT = 8000
DEFAULT_HOST = "0.0.0.0"


def get_port() -> int:
    return int(os.getenv("PORT", str(DEFAULT_PORT)))


def get_host() -> str:
    return os.getenv("HOST", DEFAULT_HOST)


def main() -> None:
    import uvicorn

    uvicorn.run("data_logger.api:app", host=get_host(), port=get_port())
