from abc import ABC, abstractmethod
from re import sub as regex_replace
from pathlib import Path
from typing import List, Type, Optional, TYPE_CHECKING

from .installation import Installation
from .containers import Container
from .verifications import Validator, TemplatedValidator
from .utils import SourceMixin

if TYPE_CHECKING:
    pass


class File(ABC):

    checker_class: "Type[Validator]"
    filename: str
    path: Path
    container: "Optional[Container]"

    def __init__(self, manager_or_container: "Installation | Container", path: Optional[Path | str] = None, **kwargs):
        """Initializes an instance of the class.

        Args:
            manager_or_container (Installation | Container): An instance of either Installation or Container.
            path (Optional[Path | str], optional): The path associated with the instance. Defaults to None.
            **kwargs: Additional keyword arguments to set as attributes on the instance.

        Raises:
            ValueError: If manager_or_container is neither an Installation nor a Container.
        """
        if isinstance(manager_or_container, Installation):
            self.container = None
            self.manager = manager_or_container
        elif isinstance(manager_or_container, Container):
            self.container = manager_or_container
            self.manager = self.container.manager
        else:
            raise ValueError(
                "Must have manager_or_container argument as either an InstallationManager, "
                f"or a ContainerCOnfig. Found {type(manager_or_container)}"
            )
        self.renderer = self.manager.renderer
        if path is not None:
            self.path = Path(path)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @abstractmethod
    def get_content(self) -> str:
        """Retrieves the content as a string. This is an abstract method that **must** be overriden in child classes.

        Returns:
            str: The content represented as a string.
        """
        return ""

    @property
    def destination_path(self):
        """Determines the destination path based on the attributes of the instance.

        This method checks for the presence of a `path` or `filename` attribute.
        If `path` is an absolute path, it is returned directly. If `filename` is provided and contains
        directory separators, a ValueError is raised. If neither attribute is absolute and the `container` is None,
        the method constructs the destination path based on the installation root or configuration path.
        If a `container` is present, it uses the container's destination path.

        Returns:
            Path: The resolved destination path.

        Raises:
            ValueError: If `filename` is a directory.
        """
        if hasattr(self, "path"):
            path = Path(self.path)
            if path.is_absolute():
                return path
        elif hasattr(self, "filename"):
            path = Path(self.filename)
            if "/" in str(path) or "\\" in str(path):
                raise ValueError("filename cannot be a directory. Use path instead in that case.")

        # if the installation file path is relative,
        # we check if there is a container management object or not to determine the complete path
        if self.container is None:
            if str(path).lstrip("./").startswith("config"):
                return self.manager.install_root_path / path
            return self.manager.config_path / path

        return self.container.destination_path / path

    @property
    def checker(self):
        """Initialize and return the checker instance for the object.

        This method checks if the instance already has a checker assigned to it.
        If not, it retrieves the `checker_kwargs` attribute (if available) and
        creates a new checker instance using the specified `checker_class`.

        Returns:
            object: The checker instance associated with the object.

        Attributes:
            _checker (object): The checker instance, initialized only once.
            checker_kwargs (dict): Optional keyword arguments for the checker.
            checker_class (type): The class used to create the checker instance.
        """
        if not hasattr(self, "_checker"):
            checker_kwargs = getattr(self, "checker_kwargs", {})
            self._checker = self.checker_class(self, **checker_kwargs)
        return self._checker

    def exists(self) -> bool:
        """Check if the destination path exists as a file.

        Returns:
            bool: True if the destination path exists and is a file, False otherwise.
        """
        return self.destination_path.is_file()

    def make_dirs(self):
        """Creates the necessary directories for the destination path.

        This method ensures that all parent directories of the specified
        destination path are created. If the directories already exist,
        no error is raised.

        Args:
            None

        Returns:
            None
        """
        self.destination_path.parent.mkdir(parents=True, exist_ok=True)

    def write_file(self, content: str):
        """Writes the specified content to a file at the destination path.

        This method ensures that the necessary directories are created before writing
        the content to the file. Upon successful creation of the file, a success message
        is rendered.

        Args:
            content (str): The content to be written to the file.

        Raises:
            IOError: If an error occurs while writing to the file.
        """
        self.make_dirs()
        with open(self.destination_path, "w") as f:
            f.write(content)
        self.renderer.success(f"The {self.destination_path.name} file has been created.")

    def make_install(self):
        """Makes the installation by writing the content to a file.

        This method retrieves the content using the `get_content` method and writes it to a file.

        Args:
            None

        Returns:
            None
        """
        self.write_file(self.get_content())

    def install(self):
        """Install the specified file if it needs to be installed.

        This method checks if the file needs to be installed and, if so, writes the content to the appropriate location.
        It also sets the title for the renderer based on the container name and filename.

        Attributes:
            container (Container): The container associated with the installation.
            renderer (Renderer): The renderer used to display the title.
            checker (Checker): The checker used to determine if installation is necessary.
            filename (str): The name of the file to be installed.

        Returns:
            None
        """
        container_name = f"{self.container.container_name}/" if self.container else ""
        self.renderer.title(f"{container_name}{self.filename}")
        if self.checker.needs_to_be_installed():
            self.write_file(self.get_content())


class TemplatedFile(File, SourceMixin):

    flag = r"%%"
    checker_class = TemplatedValidator
    keywords: List[str] = []

    def get_content(self) -> str:
        """Retrieves and processes the content from a specified source file.

        This method opens a file located at `self.source_path`, reads its contents,
        and replaces occurrences of specified keywords with their corresponding values
        using the `replace_keyword` method.

        Returns:
            str: The processed content with keywords replaced.
        """
        with open(self.source_path, "r") as f:
            contents = f.read()

        for keyword in self.keywords:
            contents = self.replace_keyword(keyword, contents)

        return contents

    def replace_keyword(self, keyword: str, content: str):
        """Replace a specified keyword in the given content with its corresponding value.

        This method checks if the provided keyword is registered in the class's keywords.
        If the keyword is not found in the class definition, it raises a ValueError.
        If the keyword is valid, it retrieves the associated value from the keywords store and replaces
        occurrences of the keyword in the content using a regex pattern.

        Args:
            keyword (str): The keyword to be replaced in the content.
            content (str): The content in which the keyword will be replaced.

        Raises:
            ValueError: If the keyword is not registered in the class's keywords.

        Returns:
            str: The content with the keyword replaced by its corresponding value.
        """
        if keyword not in self.keywords:
            raise ValueError(
                f"The use of the template keyword {keyword} was asked in {self.__class__.__name__} "
                "but no such keyword was registered as used by this file class. "
                "Please add it to maintain coherence of the installation configuration system"
            )
        value = self.manager.keywords_store[keyword]
        pattern = f"{self.flag}({keyword}){self.flag}"
        return regex_replace(pattern, str(value), content)
