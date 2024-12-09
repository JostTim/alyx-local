__version__ = "3.0.0"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, List, Any, Type
    from pathlib import Path
    from rich.text import Text


def _generate_new_secret_key(length: int = 50) -> str:
    from django.utils.crypto import get_random_string

    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%^&-_=+"
    return get_random_string(length, chars)


class InstallStatusRenderer:
    panel_style = "turquoise2"
    title = "Installation summary"

    def __init__(self, verbose=False):
        from rich.console import Console
        from rich.live import Live

        self.live = Live(console=Console(), auto_refresh=False)
        self.console = self.live.console
        self.console.print("⚙️  Installing alyx configuration files", style=self.panel_style)
        self.content: "List[Text]" = []
        self.verbose = verbose

    def print(self, text: str, style: str = "", panel_style=None, justify=None):
        from rich.text import Text

        if panel_style:
            self.panel_style = panel_style

        self.content.append(Text(text, style=style, justify=justify))
        self.render()

    def wont_create(self, file_or_folder: "str | Any"):
        if self.verbose:
            self.print(f"🫷  Won't create {file_or_folder} as it already exists. Skipping this phase.", style="grey50")

    def success(self, message: str):
        self.print(f"✅  {message}", style="bright_green")

    def warning(self, message: str):
        self.print(f"⚠️  {message}", style="dark_orange", panel_style="dark_orange")

    def done(self):
        self.clear()
        self.print(
            "💚  Your configuration is healthy, you are ready for building and running the docker app 💚",
            style="bright_green bold italic on honeydew2",
            panel_style="bright_green",
            justify="center",
        )

    def done_with_warnings(self):
        self.clear()
        self.print(
            "⚠️  Some files may contain errors as indicated above, check them if you deem necessary ⚠️",
            style="dark_orange bold italic on wheat1",
            panel_style="dark_orange",
            justify="center",
        )

    def ask(self, instruction: str, default="") -> str:
        from rich.prompt import Prompt
        from rich.text import Text

        self.clear()
        value = Prompt.ask(
            Text(f"❓ {instruction} 📝", style="dodger_blue1"),
            default=default,
            console=self.console,
        )
        self.render()
        return value

    def clear(self):
        self.live.update("")
        self.live.refresh()

    def render(self):
        from rich.panel import Panel
        from rich.console import Group

        rendering = Panel(Group(*self.content), title=self.title, title_align="left", border_style=self.panel_style)
        self.live.update(rendering)
        self.live.refresh()

    def __enter__(self):
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.live.__exit__(exc_type, exc_val, exc_tb)


def _dump_to_file(
    destination: "Path",
    content_getter: "Callable[..., str]",
    checker: "Type[FileChecker]",
    renderer: InstallStatusRenderer,
    *args,
    **kwargs,
) -> bool:

    if destination.is_file():
        renderer.wont_create(destination.name)
        return checker(destination, renderer, **kwargs).has_errors()

    content = content_getter(*args, **kwargs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w") as f:
        f.write(content)

    renderer.success(f"The {destination.name} file has been created.")
    return False


def _replace_in_file(source_file: "Path", replacements: dict = {}) -> str:
    with open(source_file, "r") as f:
        contents = f.read()

    for key, value in replacements.items():
        contents = contents.replace(key, value)

    return contents


def _create_database_password(prompter: InstallStatusRenderer) -> str:

    return prompter.ask(
        "Please enter a password for securing the postgresql database", default=_generate_new_secret_key(20)
    )


def _create_uploaded_folder(install_root: "Path", renderer: InstallStatusRenderer) -> bool:

    uploaded_folder = install_root / "docker" / "templates" / "uploaded"
    folder_to_create = ["backups", "log", "media", "static", "tables"]
    for foldername in folder_to_create:
        folder = uploaded_folder / foldername
        if folder.is_dir():
            renderer.wont_create(folder)
            continue
        folder.mkdir(parents=True)
        renderer.success(f"Created empty folder {folder} for docker copying")
    return False


def _create_rabbitmq_config_file(prompter: InstallStatusRenderer) -> str:

    username = prompter.ask(
        "Please enter a password for securing the rabbitmq database", default=_generate_new_secret_key(20)
    )

    password = prompter.ask("Please enter a username for securing the rabbitmq database", default="username")

    file_content = f"default_user = {username}\ndefault_pass = {password}"

    return file_content


class FileChecker:

    content: str
    readmode = "r"
    pending_warnings: "List[str]"

    def __init__(self, file: "Path", renderer: InstallStatusRenderer, **kwargs):
        self.path = file
        self.renderer = renderer
        self.pending_warnings = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self):
        with open(self.path, self.readmode) as f:
            self.content = f.read()

    def has_errors(self) -> bool:
        error = self.check_errors()
        if error:
            self.renderer.warning(f"File {self.path} contains errors !")
            for warning in self.pending_warnings:
                self.renderer.warning(warning)
        return error

    def check_errors(self) -> bool:
        return False


class DbPasswordChecker(FileChecker):

    def check_errors(self):
        self.read()
        return False if "\n" not in self.content and len(self.content) >= 5 else True


class RabbitConfChecker(FileChecker):

    def check_errors(self):
        self.read()
        return False


class DjangoSettingsChekcer(FileChecker):

    def check_errors(self):
        import re

        pattern = re.compile(r"^ *([A-Z_]+) *=")

        with open(self.source_file, "r") as f:  # type: ignore
            template_content = f.read()

        template_content = template_content.splitlines()
        matches = [pattern.match(line) for line in template_content]
        keywords = set([match.group(1) for match in matches if match is not None])

        self.read()
        error = False
        for keyword in keywords:
            if keyword not in self.content:
                self.pending_warnings.append(
                    f"Setting keyword {keyword} was not found in your config file but is necessary in the template."
                )
                error = True

        return error


def install_docker_alyx():

    from argparse import ArgumentParser
    from pathlib import Path
    from socket import gethostname

    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    args = parser.parse_args()

    with InstallStatusRenderer(verbose=args.verbose) as renderer:

        INSTALL_ROOT = Path(__file__).parent.parent.parent
        CONFIG_FOLDER = INSTALL_ROOT / "config"

        renderer.print(
            f"Creating the folder and files necessary for docker building in {CONFIG_FOLDER} ", style="turquoise2"
        )

        error = False
        error = error | _dump_to_file(
            CONFIG_FOLDER / "db-secure-password",
            _create_database_password,
            DbPasswordChecker,
            renderer,
            prompter=renderer,
        )

        error = error | _dump_to_file(
            CONFIG_FOLDER / "custom_settings.py",
            _replace_in_file,
            DjangoSettingsChekcer,
            renderer,
            source_file=INSTALL_ROOT / "docker" / "templates" / "custom_settings_template.py",
            replacements={"%SECRET_KEY%": _generate_new_secret_key(), "%HOSTNAME%": gethostname()},
        )

        error = error | _dump_to_file(
            CONFIG_FOLDER / "rabbitmq.conf",
            _create_rabbitmq_config_file,
            RabbitConfChecker,
            renderer,
            prompter=renderer,
        )

        _create_uploaded_folder(INSTALL_ROOT, renderer)

        if error:
            renderer.done_with_warnings()
        else:
            renderer.done()
