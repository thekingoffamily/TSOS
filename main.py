from src.settings import get_settings
from src.logger import get_logger
import uvicorn


logger = get_logger(__name__)


def main():
    settings = get_settings()
    logger.info("Starting API on %s:%s", settings.API_HOST, settings.API_PORT)
    uvicorn.run(
        "src.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
