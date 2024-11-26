__version__ = "2.0.1"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, List
    from pathlib import Path
    from rich.text import Text


def _generate_new_secret_key(length: int = 50) -> str:
    from django.utils.crypto import get_random_string

    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%^&-_=+"
    return get_random_string(length, chars)


class InstallStatusRenderer:
    panel_style = "turquoise2"
    title = "Installation summary"

    def __init__(self):
        from rich.console import Console
        from rich.live import Live

        self.live = Live(console=Console(), auto_refresh=False)
        self.console = self.live.console
        self.console.print("⚙️  Installing alyx configuration files", style=self.panel_style)
        self.content: "List[Text]" = []

    def print(self, text: str, style: str, panel_style=None):
        from rich.text import Text

        if panel_style:
            self.panel_style = panel_style

        self.content.append(Text(text, style=style))
        self.render()

    def ask(self, instruction: str, default="") -> str:
        from rich.prompt import Prompt
        from rich.text import Text

        self.clear()
        value = Prompt.ask(
            Text(instruction, style="dodger_blue1"),
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
    destination: "Path", content_getter: "Callable[..., str]", renderer: InstallStatusRenderer, *args, **kwargs
) -> bool:

    if destination.is_file():
        renderer.print(
            f"🫷  Won't create {destination.name} as it already exists. Skipping this phase.", style="grey50"
        )
        return True

    content = content_getter(*args, **kwargs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w") as f:
        f.write(content)

    renderer.print(f"✅ The {destination.name} file, has been created.", style="bright_green")
    return False


def _replace_in_file(source_file: "Path", replacements: dict = {}) -> str:
    with open(source_file, "r") as f:
        contents = f.read()

    for key, value in replacements.items():
        contents = contents.replace(key, value)

    return contents


def _create_database_password(prompter: InstallStatusRenderer) -> str:

    return prompter.ask(
        "❓ Please enter a password for securing the postgresql database. 📝", default=_generate_new_secret_key(20)
    )


def install_docker_alyx():

    from pathlib import Path

    with InstallStatusRenderer() as renderer:

        INSTALL_ROOT = Path(__file__).parent.parent.parent
        CONFIG_FOLDER = INSTALL_ROOT / "config"

        renderer.print(f"Creating the config folder files in {CONFIG_FOLDER} :", style="dark_sea_green2")

        error = False
        error = error | _dump_to_file(
            CONFIG_FOLDER / "db-secure-password", _create_database_password, renderer, prompter=renderer
        )

        error = error | _dump_to_file(
            CONFIG_FOLDER / "custom_settings.py",
            _replace_in_file,
            renderer,
            source_file=INSTALL_ROOT / "docker" / "templates" / "custom_settings_template.py",
            replacements={"%SECRET_KEY%": _generate_new_secret_key()},
        )

        if error:
            renderer.print("Some files have not been created", style="dark_orange")
            renderer.print(
                f'Check in config folder "{CONFIG_FOLDER}" if necessary.',
                style="dark_orange",
                panel_style="dark_orange",
            )
