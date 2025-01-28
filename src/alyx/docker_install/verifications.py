from abc import ABC, abstractmethod
from re import compile, search as regex_search, sub as regex_replace, escape as regex_escape
from rich.text import Text


from .utils import FileAction, FileStatus, InvalidFilePolicy, InstallStatus, SourceMixin

from typing import List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .files import File, TemplatedFile


class Validator(ABC):

    readmode = "r"
    invalid_file_policy = InvalidFilePolicy.RECREATE.value

    @abstractmethod
    def get_errors(self) -> bool:
        return FileStatus.FILE_OK.value

    content: str
    pending_warnings: "List[str | Any]"

    def __init__(self, file: "File", **kwargs):
        """Initialize a new instance.

        Args:
            file (File): The file object associated with this instance.
            **kwargs: Additional keyword arguments to set as attributes on the instance.

        Attributes:
            path (str): The destination path of the file.
            renderer: The renderer associated with the file.
            manager: The manager associated with the file.
            pending_warnings (list): A list to store any pending warnings.
        """
        self.file = file
        self.path = file.destination_path
        self.renderer = file.renderer
        self.manager = file.manager
        self.pending_warnings = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def destination_path(self):
        """Returns the destination path of the file.

        This method retrieves the destination path associated with the file
        object.

        Returns:
            str: The destination path of the file.
        """
        return self.file.destination_path

    def read(self):
        """Reads the content of a file specified by the destination path.

        This method opens the file in the specified read mode and stores its content
        in the instance variable `content`.

        Attributes:
            destination_path (str): The path to the file to be read.
            readmode (str): The mode in which to open the file (e.g., 'r' for read).
            content (str): The content read from the file.

        Raises:
            FileNotFoundError: If the file at `destination_path` does not exist.
            IOError: If an I/O error occurs while reading the file.
        """
        with open(self.destination_path, self.readmode) as f:
            self.content = f.read()

    def has_errors(self) -> bool:
        """Check if there are any errors in the current context.

        This method retrieves errors using the `get_errors` method. If errors are found, it logs a warning message
        indicating that the specified file contains errors. Additionally, it iterates through any pending warnings
        and logs them accordingly, ensuring that non-string warnings are handled appropriately.

        Returns:
            bool: True if there are errors, False otherwise.
        """
        error = self.get_errors()
        if error:
            self.renderer.warning(
                Text("File ", style="dark_orange")
                .append(f"{self.destination_path}", style=self.renderer.items_style)
                .append(" contains errors !")
            )
            for warning in self.pending_warnings:
                if not isinstance(warning, str):
                    self.renderer.warning(warning, emoji=False)
                else:
                    self.renderer.warning(warning)
        return error

    def feed_back_status(self, error: bool) -> None:
        """Updates the installation status based on the error condition.

        Args:
            error (bool): A boolean indicating whether an error has occurred.
                          If the error is of type FILE_ERROR, the installation status
                          is set to UNFINISHED_ERROR.

        Returns:
            None
        """
        if error == FileStatus.FILE_ERROR.value:
            self.manager.status = InstallStatus.UNFINISHED_ERROR

    def needs_to_be_installed(self) -> bool:
        """Determines whether a file needs to be installed based on its existence and error status.

        This method checks if the file exists and evaluates its error status. Depending on the error status and the
        defined invalid file policy, it decides whether to recreate the file, ignore it, or take no action.
        It also provides feedback through the renderer for different scenarios.

        Returns:
            bool: Indicates whether the file needs to be installed. Returns True if the file needs to be created,
              otherwise False.

        Raises:
            NotImplementedError: If the invalid file policy is not recognized.
        """
        if self.file.exists():
            error = self.has_errors()
            if error == FileStatus.FILE_ERROR.value:
                if self.invalid_file_policy == InvalidFilePolicy.RECREATE.value or self.manager.fix_mode:
                    self.renderer.warning(
                        Text("Recreating the file ", style="dark_orange").append(
                            f"{self.destination_path}", style=self.renderer.items_style
                        )
                    )
                    return FileAction.CREATE_FILE.value
                elif self.invalid_file_policy == InvalidFilePolicy.DO_NOTHING.value:
                    self.feed_back_status(error)
                    self.renderer.error(
                        Text("Ignoring the file ", style="bright_red")
                        .append(f"{self.destination_path}", style=self.renderer.items_style)
                        .append(" errors deteted to preserve your changes. You must fix the file manually.")
                    )
                    return FileAction.LET_FILE.value
                else:
                    raise NotImplementedError
            else:
                self.renderer.wont_create(self.destination_path.name)
                self.renderer.success("All good")
                return FileAction.LET_FILE.value
        return FileAction.CREATE_FILE.value


class TemplatedValidator(Validator, SourceMixin):

    file: "TemplatedFile"

    @property
    def flag(self):
        """Returns the flag attribute of the file associated with the instance.

        Returns:
            bool: The flag value of the file.
        """
        return self.file.flag

    def get_errors(self) -> bool:
        """Retrieves and checks for errors between a template file and a configuration file.

        This method compares the contents of a template file and a configuration file line by line.
        It identifies discrepancies based on predefined keywords and their expected values.
        If any mismatches are found, warnings are logged, and the method returns an error status.

        Returns:
            bool: Returns True if errors are found, otherwise returns False.
        """
        with open(self.source_path, "r") as f:
            template_content = f.read().splitlines()

        with open(self.destination_path, "r") as f:
            config_content = f.read().splitlines()

        patterns = {}
        for keyword in self.file.keywords:
            value = self.manager.keywords_store[keyword]
            pattern = f"{self.flag}({keyword}){self.flag}"
            patterns[keyword] = {"compiled": compile(pattern), "str": pattern, "expected_value": value}

        error = FileStatus.FILE_OK.value

        for line_number, (config_line, template_line) in enumerate(zip(config_content, template_content)):
            if config_line != template_line:
                for keyword, pattern in patterns.items():
                    if regex_search(pattern["compiled"], template_line):
                        extractor_pattern = regex_replace(pattern["compiled"], "(.*)", regex_escape(template_line))
                        search = regex_search(extractor_pattern, config_line)
                        if search:
                            actual_value = search.group(1)
                            if actual_value != pattern["expected_value"]:
                                self.renderer.warning(
                                    f"The line N°{line_number + 1}:{config_line.lstrip(' ')} in "
                                    f"{self.file.filename} was identified as not "
                                    f"having the same value for template keyword {keyword} "
                                    "as the one from the input_fields.json storage file. "
                                    f"Values are : {actual_value} - (actual), "
                                    f"{pattern['expected_value']} - (in store). "
                                    "Applying the changes to make one matching the other."
                                )
                                error = FileStatus.FILE_ERROR.value
                        else:
                            self.renderer.warning(
                                f"The line N°{line_number + 1}:{config_line.lstrip(' ')} in {self.file.filename} "
                                "could not been matched with the extraction pattern to identify the current value. "
                                f"(pattern used : {extractor_pattern}) Skipping"
                            )
                            error = FileStatus.FILE_ERROR.value
                        break
                else:
                    self.renderer.warning(
                        f"The line N°{line_number + 1}:{config_line.lstrip(' ')} in {self.file.filename} "
                        "doesn't match the template file "
                        "(eiher wrong position, a line added by hand, "
                        "or the residue of a previous verion configuration)"
                    )
                    error = FileStatus.FILE_ERROR.value
        return error


class AlwaysValid(Validator):

    def get_errors(self) -> bool:
        """Returns the error status of the file.

        This method checks the current file status and returns a boolean indicating
        whether there are any errors. It specifically checks if the file status is
        equal to `FileStatus.FILE_OK`.

        Returns:
            bool: True if there are errors, False if the file status is OK.
        """
        return FileStatus.FILE_OK.value
