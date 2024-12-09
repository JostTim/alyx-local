from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
import structlog

logger = structlog.get_logger(__name__)


## TODO : remove these two below


class LoggingFilesystemLoader(FilesystemLoader):
    def get_template_sources(self, template_name):
        sources = super().get_template_sources(template_name)
        for source in sources:
            logger.warning(f"FilesystemLoader checking: {source}")
        return sources


class LoggingAppDirectoriesLoader(AppDirectoriesLoader):
    def get_template_sources(self, template_name):
        sources = super().get_template_sources(template_name)
        for source in sources:
            logger.warning(f"AppDirectoriesLoader checking: {source}")
        return sources
