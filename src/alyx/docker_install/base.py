from abc import ABC, abstractmethod
from re import compile, Pattern
from pathlib import Path
from rich.text import Text
from rich.console import Console, Group
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box

from typing import List, Any, Type, Optional

FILE_ERROR = True
FILE_OK = False

CREATE_FILE = True
LET_FILE = False


class InstallStatusRenderer:
    variables_store = {}
    default_style = "blue"
    items_style = "turquoise2"

    def __init__(self, verbose=False):

        # self.live = Live(console=Console(), auto_refresh=False)
        # self.console = self.live.console
        self.console = Console()

        self.content: "List[Text]" = []
        self.verbose = verbose

    def print(self, text: str | Any, style: Optional[str] = "", justify=None):

        if style is None:
            style = self.default_style

        if isinstance(text, (Text, str)):
            text = Text("", style=style).append(text)
        self.content.append(text)
        self.render()

    def title(self, message: str, style=None, emoji=True):
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
        self.comment(f"🫷  Won't create {file_or_folder} as it already exists and has been checked as valid")

    def comment(self, message: str | Any):
        if self.verbose:
            self.print(Text("", style="grey50").append(message))

    def success(self, message: str | Any, emoji=True):
        prefix = "✔  " if emoji else ""
        self.print(Text(prefix, style="bright_green").append(message))

    def warning(self, message: str | Any, emoji=True):
        prefix = "⚠️  " if emoji else ""
        self.print(Text(prefix, style="dark_orange").append(message))

    def error(self, message: str | Any, emoji=True):
        prefix = "⛔️ " if emoji else ""
        self.print(Text(prefix, style="bright_red").append(message))

    def done(self):
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                Panel.fit(
                    Text(
                        "✔ 💚  Your configuration is healthy, you are ready "
                        "for building and running the docker app with "
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
            )
        )

    def done_with_warnings(self):
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                Panel.fit(
                    "⚠️  Some files may contain errors as indicated above, check them if you deem necessary ⚠️",
                    title="Summary",
                    box=box.SIMPLE,
                    style="wheat1",
                    border_style="wheat1" + " bold",
                ),
                box=box.HORIZONTALS,
                border_style="bright_red",
            )
        )

    def ask(self, instruction: str, default="", password_mode=False) -> str:

        if default:
            adjective = "generated" if password_mode else "default"
            password_help = Text(" (", style="turquoise2").append(
                f"press enter to keep the {adjective} one:", style="grey50"
            )
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
        live = getattr(self, "live", None)
        if live is not None:
            live.update("")
            live.refresh()

    def render(self):

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

    def __enter__(self):
        live = getattr(self, "live", None)
        if live is not None:
            live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        live = getattr(self, "live", None)
        if live is not None:
            live.__exit__(exc_type, exc_val, exc_tb)


class InstallationManager:

    variables: dict

    def __init__(self, renderer: InstallStatusRenderer, fixmode=False):
        self.renderer = renderer
        self.status = FILE_OK
        self.variables = {}
        self.fixmode = fixmode

        # This is the folder containing pyproject.toml and .git
        self.install_root_path = Path(__file__).parent.parent.parent.parent.absolute()

        self.config_path = self.install_root_path / "config"

    def delete_installation(self):

        self.renderer.title("Configuration complete deletion", style="bright_red")
        if Confirm.ask(
            Text(
                "⚠️ ⚠️ ⚠️  Are you sure that you want to reset the configuration at ",
                style="bright_red",
            )
            .append(f"{self.config_path}", self.renderer.items_style)
            .append(" ?\nPrevious configuration data in the form of ANY file in this folder ")
            .append("WILL BE LOST FOREVER !!!", style="yellow"),
            console=self.renderer.console,
        ):
            [file.unlink() for file in self.config_path.iterdir()]
            self.config_path.rmdir()
            self.renderer.success("Removed all previous configuration")

    def header(self):

        self.renderer.console.print(
            Panel.fit(
                Text("Creating the folder and files necessary for docker building in ").append(
                    f"{self.config_path}", style=self.renderer.items_style
                ),
                title="⚙️  Installing alyx configuration files",
                box=box.HORIZONTALS,
                style=self.renderer.default_style,
                border_style=self.renderer.default_style + " bold",
            )
        )

    def get_file_path(self, input_path: str | Path):
        input_path = Path(input_path)
        if input_path.is_absolute():
            return input_path
        return self.config_path / input_path

    def setup_file(
        self, destination_path: str | Path, file_class: "Type[InstallationFile]", **kwargs
    ) -> "InstallationFile":
        destination_path = self.get_file_path(destination_path)
        return file_class(destination_path, manager=self, **kwargs)

    def create_uploaded_folder(self) -> None:

        self.renderer.title("folders for shared data through containers and host")
        uploaded_folder = self.install_root_path / "docker" / "templates" / "uploaded"
        folder_to_create = ["backups", "log", "media", "static", "tables"]
        for foldername in folder_to_create:
            folder = uploaded_folder / foldername
            if folder.is_dir():
                self.renderer.wont_create(folder)
                continue
            folder.mkdir(parents=True)
            self.renderer.success(f"Created empty folder {folder} for docker copying")
        self.renderer.success("All good")

    def report_status(self):
        if self.status == FILE_ERROR:
            self.renderer.done_with_warnings()
        else:
            self.renderer.done()

    @staticmethod
    def generate_password(length: int = 15, chars="[a-Z]!#%^&-_+") -> str:
        from django.utils.crypto import get_random_string

        latin_alphabet = "abcdefghijklmnopqrstuvwxyz"

        if "[a-Z]" in chars:
            chars = chars.replace("[a-Z]", latin_alphabet + latin_alphabet.upper())

        if "[a-z]" in chars:
            chars = chars.replace("[a-z]", latin_alphabet)

        if "[A-Z]" in chars:
            chars = chars.replace("[A-Z]", latin_alphabet.upper())

        return get_random_string(length, chars)

    def add_variables(self, **kwargs):
        self.variables.update(kwargs)

    def get_variable(self, key: str):
        if key not in self.variables.keys():
            self.renderer.warning(
                f"Variable {key} was not found, it probably was not created before trying to get used."
                "Check and fix your install code."
            )
        return self.variables[key]


class InstallationFile(ABC):

    checker_class: "Type[FileChecker]"
    title: str

    @abstractmethod
    def get_content(self) -> str:
        return ""

    def __init__(self, destination_path: str | Path, manager: InstallationManager, **kwargs):
        self.manager = manager
        self.renderer = manager.renderer
        self.destination_path = Path(destination_path)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def exists(self) -> bool:
        return self.destination_path.is_file()

    def make_dirs(self):
        self.destination_path.parent.mkdir(parents=True, exist_ok=True)

    def write_file(self, content: str):
        self.make_dirs()
        with open(self.destination_path, "w") as f:
            f.write(content)
        self.renderer.success(f"The {self.destination_path.name} file has been created.")

    def make_install(self):
        self.write_file(self.get_content())

    def setup_checker(self, **kwargs) -> "FileChecker":
        return self.checker_class(self, **kwargs)


class FileChecker(ABC):

    readmode = "r"
    invalid_file_policy = "recreate"

    @abstractmethod
    def get_errors(self) -> bool:
        return FILE_OK

    content: str
    pending_warnings: "List[str | Any]"

    def __init__(self, file: InstallationFile, **kwargs):
        self.file = file
        self.path = file.destination_path
        self.renderer = file.renderer
        self.manager = file.manager
        self.pending_warnings = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self):
        with open(self.path, self.readmode) as f:
            self.content = f.read()

    def has_errors(self) -> bool:
        error = self.get_errors()
        if error:
            self.renderer.warning(
                Text("File ", style="dark_orange")
                .append(f"{self.path}", style=self.renderer.items_style)
                .append(" contains errors !")
            )
            for warning in self.pending_warnings:
                if not isinstance(warning, str):
                    self.renderer.warning(warning, emoji=False)
                else:
                    self.renderer.warning(warning)
        return error

    def feed_back_status(self, error) -> None:
        self.manager.status = self.manager.status | error

    def needs_to_be_installed(self) -> bool:
        if self.file.exists():
            error = self.has_errors()
            if error == FILE_ERROR:
                if self.invalid_file_policy == "recreate" or self.manager.fixmode:
                    self.renderer.warning(
                        Text("Recreating the file ", style="dark_orange").append(
                            f"{self.path}", style=self.renderer.items_style
                        )
                    )
                    return CREATE_FILE
                else:
                    self.feed_back_status(error)
                    self.renderer.error(
                        Text("Ignoring the file ", style="bright_red")
                        .append(f"{self.path}", style=self.renderer.items_style)
                        .append(" errors deteted to preserve your changes. You must fix the file manually.")
                    )
                    return LET_FILE
            else:
                self.renderer.wont_create(self.file.destination_path.name)
                self.renderer.success("All good")
                return LET_FILE
        return CREATE_FILE

    def make_install(self) -> None:
        self.renderer.title(f"{self.file.title}")
        if self.needs_to_be_installed() == CREATE_FILE:
            self.file.make_install()


class ReplaceTemplateInstallationFile(InstallationFile):

    source_file: Path
    replacements: dict

    def get_content(self) -> str:
        with open(self.source_file, "r") as f:
            contents = f.read()

        for key, value in self.replacements.items():
            contents = contents.replace(key, value)

        return contents


class ReplaceTemplateChecker(FileChecker):

    pattern: Pattern
    source_file: Path

    invalid_file_policy = "ignore"

    def get_errors(self) -> bool:

        if isinstance(self.pattern, str):
            self.pattern = compile(self.pattern)

        with open(self.source_file, "r") as f:  # type: ignore
            template_content = f.read()

        template_content = template_content.splitlines()
        matches = [self.pattern.match(line) for line in template_content]
        keywords = set([match.group(1) for match in matches if match is not None])
        self.read()
        error = FILE_OK
        for keyword in keywords:
            if keyword not in self.content:
                self.pending_warnings.append(
                    Text("Setting keyword ", style="dark_orange")
                    .append(keyword, style=self.renderer.items_style)
                    .append(" was not found in your config file")
                )
                error = FILE_ERROR

        if error == FILE_ERROR:
            self.pending_warnings.append(
                Text("But they are necessary according to the template at ", style="dark_orange").append(
                    str(self.source_file), style=self.renderer.items_style
                )
            )
        return error


class KeysChecker(FileChecker):
    keys: set

    invalid_file_policy = "ignore"

    def get_errors(self) -> bool:

        self.read()
        error = FILE_OK
        for keyword in self.keys:
            if keyword not in self.content:
                self.pending_warnings.append(
                    Text("Setting keyword ", style="dark_orange")
                    .append(keyword, style=self.renderer.items_style)
                    .append(" was not found in your config file")
                )
                error = FILE_ERROR

        if error == FILE_ERROR:
            self.pending_warnings.append(Text("But they are necessary", style="dark_orange"))
        return error


class NoCheck(FileChecker):

    def get_errors(self) -> bool:
        return FILE_OK
