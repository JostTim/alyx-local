from argparse import Namespace
import json
from pathlib import Path
from rich.text import Text
from rich.console import Console, Group
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import box

from .utils import InstallStatus

from typing import List, Any, Type, Optional, Set, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .containers import Container
    from .files import File


class Renderer:
    variables_store = {}
    default_style = "blue"
    items_style = "turquoise2"
    max_width = 120

    def __init__(self, verbose=False):
        """Initializes the class with optional verbosity and sets up the console.

        Args:
            verbose (bool, optional): If True, enables verbose output. Defaults to False.

        Attributes:
            console (Console): An instance of the Console class for output.
            content (List[Text]): A list to hold text content.
            verbose (bool): Indicates whether verbose output is enabled.
        """

        # self.live = Live(console=Console(), auto_refresh=False)
        # self.console = self.live.console
        self.console = Console()

        self.content: "List[Text]" = []
        self.verbose = verbose

    def print(self, text: str | Any, style: Optional[str] = "", justify=None):
        """Prints the given text with the specified style and justification.

        Args:
            text (str | Any): The text to be printed. Can be a string or any other type.
            style (Optional[str], optional): The style to apply to the text. Defaults to an empty string,
                which will use the default style if not provided.
            justify (optional): The justification for the text. The default behavior is determined by
                the implementation.

        Returns:
            None: This function does not return a value.

        Raises:
            TypeError: If the text is not of type str or Text.
        """

        if style is None:
            style = self.default_style

        if isinstance(text, (Text, str)):
            text = Text("", style=style).append(text)
        self.content.append(text)
        self.render()

    def title(self, message: str, style=None, emoji=True):
        """Display a title message with optional styling and emoji prefix.

        Args:
            message (str): The message to be displayed as a title.
            style (str, optional): The style to be applied to the title. If None, the default style is used.
              Defaults to None.
            emoji (bool, optional): Whether to prepend an emoji to the title based on the style.
              Defaults to True.

        Returns:
            None: This function does not return a value; it prints the formatted title message.
        """

        if style is None:
            style = self.default_style

        if emoji:
            if "bright_red" in style:
                prefix = "\n🔴 "
            else:
                prefix = "\n🔵 "
        else:
            prefix = "\n"

        self.print(Text(prefix, style=style).append(message, style="underline " + style))

    def wont_create(self, file_or_folder: "str | Any"):
        """Logs a message indicating that a file or folder will not be created because it already exists and
        has been validated.

        Args:
            file_or_folder (str | Any): The name of the file or folder that won't be created.
        """
        self.comment(f"🫷  Won't create {file_or_folder} as it already exists and has been checked as valid")

    def comment(self, message: str | Any):
        """Logs a comment message if verbose mode is enabled.

        Args:
            message (str | Any): The message to be logged. Can be a string or any other type.

        Returns:
            None
        """
        if self.verbose:
            self.print(Text("", style="grey50").append(message))

    def success(self, message: str | Any, emoji=True):
        """Logs a success message with an optional emoji prefix.

        Args:
            message (str | Any): The message to be logged as a success. Can be a string or any other type.
            emoji (bool, optional): If True, prepends a checkmark emoji to the message. Defaults to True.

        Returns:
            None
        """
        prefix = "✔  " if emoji else ""
        self.print(Text(prefix, style="bright_green").append(message))

    def warning(self, message: str | Any, emoji=True):
        """Displays a warning message with an optional emoji prefix.

        Args:
            message (str | Any): The warning message to be displayed. Can be a string or any other type.
            emoji (bool): If True, prepends a warning emoji to the message. Defaults to True.

        Returns:
            None
        """
        prefix = "⚠️  " if emoji else ""
        self.print(Text(prefix, style="dark_orange").append(message))

    def error(self, message: str | Any, emoji=True):
        """Logs an error message with an optional emoji prefix.

        Args:
            message (str | Any): The error message to be logged. Can be a string or any other type.
            emoji (bool): If True, prepends an emoji to the error message. Defaults to True.

        Returns:
            None
        """
        prefix = "⛔️ " if emoji else ""
        self.print(Text(prefix, style="bright_red").append(message))

    def done(self):
        """Prints a summary message indicating that the configuration is healthy and ready for building and running
        the Docker application.

        This method displays a formatted message in the console, including instructions for building the application
        using specific commands. The message is styled with a bright green color to indicate success.

        Attributes:
            console: The console object used for printing messages.
            items_style: The style applied to specific text items in the message.

        Usage:
            Call this method when the configuration check is complete and successful.
        """
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                Panel.fit(
                    Text(
                        "✔ 💚  Your configuration is healthy, you are ready "
                        "for building and running the docker app with ",
                        justify="center",
                    )
                    .append("pdm run fresh-build-fast", style=self.items_style)
                    .append(" or other build commands ( list all commands with ")
                    .append("pdm run -l", style=self.items_style)
                    .append(" ) 💚 ✔"),
                    title="Summary",
                    box=box.SIMPLE,
                    style="bright_green",
                    border_style="bright_green" + " bold",
                ),
                box=box.HORIZONTALS,
                border_style="bright_green",
                width=self.max_width,
            )
        )

    def done_with_warnings(self):
        """Displays a warning message indicating that some files may contain errors.

        This method prints a summary panel to the console, alerting the user to check
        the files for potential issues. The message is styled with specific colors and
        border styles for emphasis.

        Args:
            self: The instance of the class that this method belongs to.

        Returns:
            None
        """
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                Panel.fit(
                    Text(
                        "⚠️  Some files may contain errors as indicated above, check them if you deem necessary ⚠️",
                        justify="center",
                    ),
                    title="Summary",
                    box=box.SIMPLE,
                    style="wheat1",
                    border_style="wheat1" + " bold",
                ),
                box=box.HORIZONTALS,
                border_style="bright_red",
                width=self.max_width,
            )
        )

    def unfinished_installation(self):
        """Displays a warning message indicating that the configuration did not finish correctly.

        This method prints a formatted panel to the console, alerting the user to an unfinished
        installation process. The message is styled with specific colors and borders to draw
        attention to the issue.

        Attributes:
            console: The console object used for printing messages.
        """
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                Panel.fit(
                    Text("⚠️  The configuration didn't finished correctly ⚠️", justify="center"),
                    title="Summary",
                    box=box.SIMPLE,
                    style="wheat1",
                    border_style="wheat1" + " bold",
                ),
                box=box.HORIZONTALS,
                border_style="bright_red",
                width=self.max_width,
            )
        )

    def ask(
        self,
        instruction: str,
        manager: "Installation",
        default="",
        password_mode=False,
    ) -> str:
        """Ask the user for input based on a given instruction.

        Args:
            instruction (str): The instruction or prompt to display to the user.
            manager (Installation): An instance of the Installation manager that may control input behavior.
            default (str, optional): The default value to use if the user does not provide input.
              Defaults to an empty string.
            password_mode (bool, optional): If True, the input will be treated as a password and not displayed.
              Defaults to False.

        Returns:
            str: The user's input or the default value if no input is provided.
        """

        if default:
            adjective = "generated" if password_mode else "default"
            password_help = Text(" (", style="turquoise2").append(
                f"press enter to use the {adjective} one:", style="grey50"
            )
            if manager.no_input_mode:
                return default
        else:
            password_help = ""

        value = Prompt.ask(
            Text("", style="bright_yellow").append("❓ ").append(instruction).append(password_help),
            default=default,
            console=self.console,
            password=password_mode,
        )
        return value

    def clear(self):
        """Clears the content of the 'live' attribute if it exists.

        This method checks if the 'live' attribute is present in the instance.
        If it is, it updates its content to an empty string and refreshes it.

        Attributes:
            live (optional): An attribute that is expected to have 'update'
            and 'refresh' methods.

        Returns:
            None
        """
        live = getattr(self, "live", None)
        if live is not None:
            live.update("")
            live.refresh()

    def render(self):
        """Render the content to the console or update the live display.

        This method checks if a live display is available. If it is, it creates a
        Panel with the current content and updates the live display. If not, it
        prints the last item of the content to the console.

        Attributes:
            live (Live): An optional live display object that can be updated.

        Raises:
            AttributeError: If 'live' attribute is not found on the instance.
        """

        live = getattr(self, "live", None)

        if live is not None:
            rendering = Panel(
                Group(*self.content),
                box=box.SIMPLE,
            )
            live.update(rendering)
            live.refresh()
        else:
            self.console.print(self.content[-1])

    def header(self, installation: "Installation"):
        """Creates and displays a header panel indicating the installation of Alyx configuration files.

        Args:
            installation (Installation): An instance of the Installation class containing configuration details,
                                          including the path where the configuration files will be created.

        Returns:
            None
        """
        self.console.print(
            Panel.fit(
                Text("Creating the folder and files necessary for docker building in ", justify="center").append(
                    f"{installation.config_path}",
                    style=self.items_style,
                ),
                title="⚙️  Installing alyx configuration files",
                box=box.HORIZONTALS,
                style=self.default_style,
                border_style=self.default_style + " bold",
                width=self.max_width,
            )
        )

    def report_status(self, installation: "Installation"):
        """Reports the status of the given installation.

        This method checks the status of the provided installation and takes appropriate actions based on its state.
        If the installation status is an error, it calls `done_with_warnings()`.
        For unknown or unfinished error statuses, it calls `unfinished_installation()`.
        If the installation is successful, it calls `done()`.
        If the status is not recognized, it raises a `NotImplementedError`.

        Args:
            installation (Installation): The installation object whose status is to be reported.

        Raises:
            NotImplementedError: If the installation status is not recognized.
        """
        if installation.status == InstallStatus.ERROR:
            self.done_with_warnings()
        elif installation.status in [InstallStatus.UNKNOWN, InstallStatus.UNFINISHED_ERROR, InstallStatus.UNFINISHED]:
            self.unfinished_installation()
        elif installation.status == InstallStatus.SUCCESS:
            self.done()
        else:
            raise NotImplementedError

    def __enter__(self):
        """Context manager entry method.

        This method is called when entering the runtime context related to this object.
        If the object has a 'live' attribute, it will also call the `__enter__` method
        of that attribute.

        Returns:
            self: The instance of the class, allowing for method chaining.
        """
        live = getattr(self, "live", None)
        if live is not None:
            live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handles the exit of a context manager.

        This method is called when the execution of a `with` statement is finished.
        It allows for cleanup actions to be performed, such as releasing resources
        or handling exceptions.

        Args:
            exc_type (type): The exception type raised in the `with` block,
                             or None if no exception was raised.
            exc_val (Exception): The exception instance raised in the `with` block,
                                 or None if no exception was raised.
            exc_tb (traceback): The traceback object associated with the exception,
                                or None if no exception was raised.

        Returns:
            None
        """
        live = getattr(self, "live", None)
        if live is not None:
            live.__exit__(exc_type, exc_val, exc_tb)


class KeywordsStore(dict):

    filename = "input_fields.json"

    def __init__(self, *args, manager: "Installation", **kwargs):
        """Initialize the class with a manager.

        Args:
            *args: Variable length argument list for the superclass initialization.
            manager (Installation): An instance of the Installation class that manages this instance.
            **kwargs: Variable length keyword argument list for the superclass initialization.
        """
        super().__init__(*args, **kwargs)
        self.manager = manager

    @property
    def path(self):
        """Returns the full path to the configuration file.

        This method constructs the full path by combining the configuration
        directory path managed by the manager with the filename of the
        configuration file.

        Returns:
            Path: The full path to the configuration file.
        """
        return self.manager.config_path / self.filename

    def __setitem__(self, key, value):
        """Sets the value for a given key in the object and saves the state.

        Args:
            key: The key for which the value is to be set.
            value: The value to be associated with the key.

        This method overrides the default behavior of setting an item by calling
        the superclass's __setitem__ method and then saving the current state
        of the object.
        """
        super().__setitem__(key, value)
        self.save()

    def __getitem__(self, key):
        """Retrieve an item from the KeywordsStore.

        This method overrides the __getitem__ method to fetch a keyword from the
        KeywordsStore. If the manager is in reconfiguration mode or the key is not
        present, it loads the necessary data and retrieves the value using a getter
        function.

        Args:
            key (str): The key for the item to retrieve from the KeywordsStore.

        Returns:
            The value associated with the specified key.

        Raises:
            KeyError: If the key is not found in the KeywordsStore after attempting
            to retrieve it.

        Notes:
            This method logs a comment indicating the retrieval of the keyword and
            the current state of the KeywordsStore.
        """
        if not self.manager.reconfigure:
            self.load()
        self.manager.renderer.comment(f"Getting keyword {key} from the KeywordsStore containing {dict(self)}")
        if self.manager.reconfigure or key not in self.keys():
            getter = self.get_keyword_getter(key)
            value = getter()
            self[key] = value
        return super().__getitem__(key)

    def load(self, key=None):
        """Load data from a JSON file into the object.

        This method reads a JSON file from the specified path and loads its contents into the object.
        If a specific key is provided, only the value associated with that key will be loaded.
        If the key is not found or if no key is specified, all key-value pairs from the JSON file will be loaded.

        Args:
            key (str, optional): The specific key to load from the JSON file.
                                 If None, all key-value pairs will be loaded.

        Returns:
            None: This method does not return a value.

        Raises:
            FileNotFoundError: If the specified path does not point to a valid file.
        """
        if not self.path.is_file():
            return
        with open(self.path, "r") as f:
            fields = json.load(f)
        for loaded_key, value in fields.items():
            if key is None or loaded_key == key:
                super().__setitem__(loaded_key, value)

    def save(self):
        """Saves the current object state to a JSON file.

        This method creates the necessary parent directories for the file if they do not exist,
        and then writes the object's dictionary representation to the specified path in JSON format
        with an indentation of 4 spaces.

        Attributes:
            path (Path): The file path where the object state will be saved.

        Raises:
            IOError: If there is an error writing to the file.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(dict(self), f, indent=4)

    def get_keyword_getter(self, keyword) -> Callable[..., str]:
        """Retrieves a getter method for a specified keyword from the manager.

        This function looks for a method in the manager associated with the given keyword.
        If the method is not found, it raises a ValueError.

        Args:
            keyword (str): The name of the keyword for which to retrieve the getter method.

        Returns:
            Callable[..., str]: The getter method associated with the specified keyword.

        Raises:
            ValueError: If no getter method is configured for the specified keyword.
        """
        getter = getattr(self.manager, keyword, None)
        if getter is None:
            raise ValueError(f"You didn't configured a getter method for the variable {keyword}")
        return getter

    @property
    def keywords_list(self) -> Set[str]:
        from .files import TemplatedFile

        keywords = [
            keyword
            for container in self.manager.containers
            for file in container.files
            if isinstance(file, TemplatedFile)
            for keyword in file.keywords
        ]
        keywords.extend(
            [keyword for file in self.manager.files if isinstance(file, TemplatedFile) for keyword in file.keywords]
        )
        return set(keywords)

    def validate_keywords_list(self):
        for keyword in self.keywords_list:
            if not hasattr(self.manager, keyword):
                raise ValueError(f"You didn't configured a getter method for the variable {keyword}")

    def populate(self):
        for keyword in self.keywords_list:
            self[keyword]


class Installation:

    keywords_store: KeywordsStore
    containers_classes: "List[Type[Container]]" = []
    files_classes: "List[Type[File]]" = []

    # options settable from command line :
    delete: bool  # A flag indicating whether to enable delete mode. Defaults to False.
    verbose: bool  # A flag indicating whether to enable verbose output. Defaults to False.
    reconfigure: bool  # A flag indicating whether to allow reconfiguration. Defaults to False.
    no_input_mode: bool  # A flag indicating whether to enable no input mode. Defaults to False.
    fix_mode: bool  # A flag indicating whether to enable fix mode. Defaults to False.

    @classmethod
    def from_arguments(cls, arguments: Namespace):
        """Creates an instance of the class from the provided command line arguments.

        Args:
            cls (type): The class to instantiate.
            arguments (Namespace): An object containing command line arguments.

        Returns:
            cls: An instance of the class initialized with the specified arguments.

        Raises:
            Exception: If any required argument is missing or invalid.

        Notes:
            - The function modifies the `arguments` object based on certain conditions
              before passing it to the class constructor.
            - The `delete_noinput` argument, if set to True,
              will automatically set both `noinput` and `delete` to True.
        """
        fix_mode = arguments.fix
        if arguments.delete_noinput:
            arguments.noinput = True
            arguments.delete = True
        if arguments.inputs_only:
            arguments.no_input_mode = False
        delete = arguments.delete
        no_input_mode = arguments.noinput
        verbose = arguments.verbose
        reconfigure = arguments.force
        inputs_only = arguments.inputs_only

        return cls(
            fix_mode=fix_mode,
            no_input_mode=no_input_mode,
            inputs_only=inputs_only,
            verbose=verbose,
            reconfigure=reconfigure,
            delete=delete,
        )

    def __init__(
        self,
        renderer: Optional[Renderer] = None,
        fix_mode=False,
        no_input_mode=False,
        inputs_only=False,
        verbose=False,
        reconfigure=False,
        delete=False,
    ):
        """Initializes an instance of the class.

        Args:
            renderer (Optional[Renderer]): An optional renderer instance. If not provided, a new Renderer
              will be created with the specified verbosity.
            fix_mode (bool): A flag indicating whether to enable fix mode. Defaults to False.
            no_input_mode (bool): A flag indicating whether to enable no input mode. Defaults to False.
            verbose (bool): A flag indicating whether to enable verbose output. Defaults to False.
            reconfigure (bool): A flag indicating whether to allow reconfiguration. Defaults to False.
            delete (bool): A flag indicating whether to enable delete mode. Defaults to False.

        Attributes:
            renderer (Renderer): The renderer instance used by the class.
            status (InstallStatus): The installation status, initialized to UNKNOWN.
            keywords_store (KeywordsStore): An instance of KeywordsStore, initialized with the current manager.
            fix_mode (bool): The current state of fix mode.
            no_input_mode (bool): The current state of no input mode.
            reconfigure (bool): The current state of reconfiguration.
            delete (bool): The current state of delete mode.
        """

        if renderer is None:
            renderer = Renderer(verbose=verbose)

        self.renderer = renderer
        self.status = InstallStatus.UNKNOWN
        self.keywords_store = KeywordsStore(manager=self)
        self.fix_mode = fix_mode
        self.no_input_mode = no_input_mode
        self.inputs_only_mode = inputs_only
        self.reconfigure = reconfigure
        self.delete = delete

    @property
    def install_root_path(self):
        """Returns the absolute path to the root directory of the project.

        This directory is expected to contain the `pyproject.toml` file and the `.git` directory.

        Returns:
            Path: The absolute path to the root directory.
        """
        return Path(__file__).parent.parent.parent.parent.absolute()

    @property
    def docker_path(self):
        """Returns the path to the Docker installation directory.

        This method constructs the path by appending "docker" to the
        install root path of the instance.

        Returns:
            Path: The full path to the Docker installation directory.
        """
        return self.install_root_path / "docker"

    @property
    def config_path(self):
        """Returns the path to the configuration directory.

        This method constructs the path to the 'config' directory
        by appending it to the install root path.

        Returns:
            Path: The full path to the configuration directory.
        """
        return self.install_root_path / "config"

    @property
    def compose_path(self):
        """Returns the path to the compose.yaml file.

        This method constructs the full path to the 'compose.yaml' file
        by appending it to the install root path.

        Returns:
            Path: The full path to the 'compose.yaml' file.
        """
        return self.install_root_path / "compose.yaml"

    @property
    def containers(self) -> "List[Container]":
        """Returns a list of container instances.

        This method initializes the `_containers` attribute with instances of
        container classes defined in `containers_classes` if it has not been
        initialized yet. It then returns the list of container instances.

        Returns:
            List[Container]: A list of container instances.
        """
        if not hasattr(self, "_containers"):
            self._containers = [cls(self) for cls in self.containers_classes]
        return self._containers

    @property
    def files(self):
        """Retrieve a list of file instances.

        This method checks if the instance has a cached list of file instances.
        If not, it creates the list by instantiating each class defined in
        `files_classes` and stores it in the `_files` attribute.

        Returns:
            list: A list of instantiated file objects.
        """
        if not hasattr(self, "_files"):
            self._files = [cls(self) for cls in self.files_classes]
        return self._files

    def install(self):
        """Installs the necessary components and updates the installation status.

        This method validates the keywords list, populates the keywords store, and installs
        all containers and files associated with the current instance. It also manages the
        reconfiguration state and updates the installation status based on predefined conditions.

        Attributes:
            reconfigure (bool): Indicates whether the installation should be reconfigured.
            containers (list): A list of container objects to be installed.
            files (list): A list of file objects to be installed.
            status (InstallStatus): The current status of the installation process.

        Raises:
            Any exceptions raised during the installation of containers or files will propagate
            to the caller.
        """
        self.keywords_store.validate_keywords_list()
        self.keywords_store.populate()
        if self.inputs_only_mode:
            self.status = InstallStatus.UNFINISHED
            return
        # once we asked everything, we set reconfigure to False if it was True, to avoid re-asking answers again
        self.reconfigure = False

        for container in self.containers:
            container.install()
        for file in self.files:
            file.install()
        if self.status == InstallStatus.UNFINISHED_ERROR:
            self.status = InstallStatus.ERROR
        if self.status == InstallStatus.UNKNOWN:
            self.status = InstallStatus.SUCCESS

    def __enter__(
        self,
    ):
        """Context manager entry method.

        This method is called when entering the runtime context related to this object.
        It initializes the renderer and sets up the header.

        Returns:
            self: The instance of the class, allowing for method chaining.
        """
        self.renderer = self.renderer.__enter__()
        self.renderer.header(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handles the exit of a context manager by reporting the status and delegating to the renderer's exit method.

        Args:
            exc_type (type): The exception type raised in the context, or None if no exception occurred.
            exc_val (Exception): The exception instance raised in the context, or None if no exception occurred.
            exc_tb (traceback): The traceback object associated with the exception, or None if no exception occurred.

        Returns:
            bool: Indicates whether the exception should be suppressed (True) or propagated (False).
        """
        self.renderer.report_status(self)
        self.renderer.__exit__(exc_type, exc_val, exc_tb)


class InstallationUtilities:

    renderer: Renderer
    config_path: Path
    install_root_path: Path
    no_input_mode: bool

    @staticmethod
    def generate_password(length: int = 15, chars="[a-Z][0-9]!%^&-_+", alphanum=False) -> str:
        """Generate a random password of specified length using given character set.

        Args:
            length (int, optional): The length of the generated password. Defaults to 15.
            chars (str, optional): A string representing the characters to use in the password.
                It can include placeholders like "[a-Z]", "[0-9]", "[A-Z]", and "[a-z]".
                Defaults to "[a-Z][0-9]!%^&-_+".
            alphanum (bool, optional): If True, the character set will be limited to alphanumeric
                characters only (equivalent to "[a-Z][0-9]"). Defaults to False.

        Returns:
            str: A randomly generated password of the specified length.
        """
        from django.utils.crypto import get_random_string

        if alphanum:  # boolean flag shortcut for "[a-Z][0-9]"
            chars = "[a-Z][0-9]"

        latin_alphabet = "abcdefghijklmnopqrstuvwxyz"
        numbers = "1234567890"

        if "[a-Z]" in chars:
            chars = chars.replace("[a-Z]", latin_alphabet + latin_alphabet.upper())

        if "[a-z]" in chars:
            chars = chars.replace("[a-z]", latin_alphabet)

        if "[A-Z]" in chars:
            chars = chars.replace("[A-Z]", latin_alphabet.upper())

        if "[0-9]" in chars:
            chars = chars.replace("[0-9]", numbers)

        return get_random_string(length, chars)

    def create_data_folder(self) -> None:
        """Creates a data folder structure for shared and persistent data.

        This method initializes a main data folder at the specified installation root path,
        and creates subfolders for backups, logs, and tables. If a subfolder already exists,
        it notifies the user that the folder will not be created. Upon successful creation
        of each folder, a success message is displayed.

        Attributes:
            renderer: An object responsible for rendering messages to the user.

        Returns:
            None
        """

        self.renderer.title("folders for shared and persistent data through containers and host")
        data_folder = self.install_root_path / "data"
        sub_folders_to_create = ["backups", "logs", "tables"]
        for foldername in sub_folders_to_create:
            folder = data_folder / foldername
            if folder.is_dir():
                self.renderer.wont_create(folder)
                continue
            folder.mkdir(parents=True)
            self.renderer.success(f"Created empty folder {folder} for docker copying")
        self.renderer.success("All good")

    def delete_configuration(self):
        """Deletes the configuration folder and its contents.

        This method prompts the user for confirmation before proceeding with the deletion of the configuration folder.
        If the folder does not exist, a success message is displayed indicating that there is no
        configuration to remove. If the user confirms the deletion, all files and subdirectories within the
        configuration folder are removed recursively.

        Raises:
            KeyboardInterrupt: If the user does not confirm the deletion when prompted.

        Returns:
            None
        """

        def empty_folder_content(folder: Path):
            [file.unlink() for file in folder.iterdir() if file.is_file()]
            [empty_folder_content(subfolder) for subfolder in folder.iterdir() if subfolder.is_dir()]
            folder.rmdir()

        self.renderer.title("Configuration complete deletion", style="bright_red")

        if not self.config_path.exists():
            self.renderer.success("No configuration folder to remove. Done.")
            return

        if self.no_input_mode or (
            Confirm.ask(
                Text(
                    "⚠️ ⚠️ ⚠️  Are you sure that you want to reset the configuration at ",
                    style="bright_red",
                )
                .append(f"{self.config_path}", self.renderer.items_style)
                .append(" ?\nPrevious configuration data in the form of ANY file in this folder ")
                .append("WILL BE LOST FOREVER !!!", style="yellow"),
                console=self.renderer.console,
            )
        ):
            empty_folder_content(self.config_path)
            self.renderer.success("Removed all previous configuration")
        else:
            raise KeyboardInterrupt(
                "The configuration process was stopped because you added a --delete "
                "option but didn't confirm the deletion when asked for."
            )
