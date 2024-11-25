__version__ = "2.0.1"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable


def _generate_new_secret_key(length: int = 50) -> str:
    from django.utils.crypto import get_random_string

    chars = "abcdefghijklmnopqrstuvwxyz0123456789!#$%^&*(-_=+)"
    return get_random_string(length, chars)


def _dump_to_file(destination: "Path", content_getter: "Callable[..., str]", *args, **kwargs) -> None:

    from rich.console import Console

    console = Console()
    if destination.is_file():
        console.print(f"🫷  Cannot create {destination.name} if it already exists. Skipping it.", style="grey50")
        console.print(f"Check in folder {destination.parent} if necessary.", style="grey3")

    content = content_getter(*args, **kwargs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w") as f:
        f.write(content)

    console.print(f"✅ The {destination.name} file, has been created.", style="bright_green")


def _replace_in_file(source_file: "Path", replacements: dict = {}) -> str:
    with open(source_file, "r") as f:
        contents = f.read()

    for key, value in replacements.items():
        contents = contents.replace(key, value)

    return contents


def _create_database_password() -> str:
    from rich.prompt import Prompt
    from rich.text import Text

    return Prompt.ask(
        Text("❓ Please enter a password for securing the postgresql database. 📝", style="blue"),
        default=_generate_new_secret_key(20),
    )


def install_docker_alyx():

    from pathlib import Path

    INSTALL_ROOT = Path(__file__).parent.parent.parent

    _dump_to_file(
        INSTALL_ROOT / "config" / "db-secure-password",
        _create_database_password,
    )

    _dump_to_file(
        INSTALL_ROOT / "config" / "custom_settings.py",
        _replace_in_file,
        replacements={"%SECRET_KEY%": _generate_new_secret_key()},
    )
