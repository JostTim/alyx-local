from enum import Enum
from pathlib import Path

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .installation import Installation
    from .containers import Container


class FileAction(Enum):
    CREATE_FILE = True
    LET_FILE = False


class FileStatus(Enum):
    FILE_ERROR = True
    FILE_OK = False


class InstallStatus(Enum):
    UNKNOWN = 0
    SUCCESS = 1
    ERROR = 2
    UNFINISHED_ERROR = 3
    UNFINISHED = 4


class InvalidFilePolicy(Enum):
    DO_NOTHING = 0
    RECREATE = 1


class SourceMixin:
    """This is a mixin to be used with File class to make a
    class that requires a source file (template) to generate a desination file

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    source_file: Path | str
    manager: "Installation"
    container: "Optional[Container]"

    @property
    def source_path(self):
        """Determines the source path of the file associated with the current instance.
        (either of a File or Validator class and child classes). Use it as a mixin to provide access to a source
        file that relates to the destination file, for file-templated File and Validator classes.

        This method checks the type of the current instance and its associated file to
        return the appropriate source path. It handles various scenarios including
        validation of file types and the presence of absolute or relative paths.

        Returns:
            Path: The source path of the file.

        Raises:
            ValueError: If the validator is used with a file that does not inherit from
            SourceFile, or if an absolute path is provided without a corresponding
            absolute source_file.

        Notes:
            - The method requires that both Validator and File inherit from SourceFile
              when using the source_path attribute.
            - If the instance has a container, the source path is determined based on
              the container's source path.
        """
        from .verifications import Validator

        if isinstance(self, Validator):
            if isinstance(self.file, SourceMixin):
                return self.file.source_path
            else:
                raise ValueError(
                    f"The validator {self.__class__.__name__} is used for a "
                    f"file {self.file.__class__.__name__} that doesn't seem to inherit from SourceFile. "
                    "Please make sure both Validator and File inherits "
                    "from SourceFIle is you use the source_path attribute."
                )

        if hasattr(self, "source_file"):
            source_file = Path(self.source_file)
            if source_file.is_absolute():
                return source_file
        elif hasattr(self, "path"):
            source_file = Path(getattr(self, "path"))
            if source_file.is_absolute():
                raise ValueError(
                    "If you use an absolute value for path to specify where the file sits, "
                    "you must supply an absolute value for source_file too."
                )
        elif hasattr(self, "filename"):
            source_file = Path(getattr(self, "filename"))

        # If we arrive there, source_file is a relative path, we determine
        # it's root depending of if there is a container or not.
        if self.container is None:
            if str(source_file).lstrip("./").startswith("docker"):
                return self.manager.install_root_path / source_file
            return self.manager.docker_path / source_file
        return self.container.source_path / source_file
