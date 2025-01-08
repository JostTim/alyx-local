from argparse import ArgumentParser
from pathlib import Path
from socket import gethostname
from tzlocal import get_localzone
from .base import (
    InstallStatusRenderer,
    InstallationManager,
    InstallationFile,
    FileChecker,
    ReplaceTemplateChecker,
    ReplaceTemplateInstallationFile,
    KeysChecker,
    NoCheck,
    FILE_OK,
    FILE_ERROR,
)


class DbPasswordFile(InstallationFile):
    title = "db-secure-password"

    def get_content(self):
        return self.renderer.ask(
            "Please enter a password for securing the postgresql database",
            default=self.manager.generate_password(
                20, chars="[a-Z][0-9]"
            ),  # no special chars as they fuck up the connection with pg_dumb through dbbackup
            password_mode=True,
        )

    class DbPasswordChecker(FileChecker):
        def get_errors(self):
            self.read()
            return FILE_OK if "\n" not in self.content and len(self.content) >= 5 else FILE_ERROR

    checker_class = DbPasswordChecker


class DjangoSettingsFile(ReplaceTemplateInstallationFile):
    title = "custom_settings.py"
    checker_class = ReplaceTemplateChecker


class ServersJsonFile(ReplaceTemplateInstallationFile):
    title = "servers.json"
    checker_class = ReplaceTemplateChecker


class CeleryEnvFile(InstallationFile):
    title = "celery.env"

    def get_content(self):
        username = self.manager.get_variable("rabbitmq_username")
        password = self.manager.get_variable("rabbitmq_password")

        lines = [
            f"RABBITMQ_USER={username}",
            f"RABBITMQ_PASSWORD={password}",
            f"FLOWER_USER={username}",
            f"FLOWER_PASSWORD={password}",
        ]
        file_content = "\n".join(lines)
        return file_content

    checker_class = KeysChecker


class PgadminEnvFile(InstallationFile):
    title = "pgadmin.env"

    def get_content(self) -> str:

        username = self.renderer.ask(
            "Please enter a username for securing the pgadmin management web interface",
            default="admin@admin.com",
        )

        password = self.renderer.ask(
            "Please enter a password for securing the pgadmin management web interface",
            default=self.manager.generate_password(20),
            password_mode=True,
        )

        lines = [
            f"PGADMIN_DEFAULT_EMAIL={username}",
            f"PGADMIN_DEFAULT_PASSWORD={password}",
        ]
        file_content = "\n".join(lines)
        return file_content

    checker_class = KeysChecker


class RabbitmqConfFile(InstallationFile):
    title = "rabbitmq.conf"

    def get_content(self):
        username = self.renderer.ask(
            "Please enter a username for securing the rabbitmq database",
            default="username",
        )

        password = self.renderer.ask(
            "Please enter a password for securing the rabbitmq database",
            default=self.manager.generate_password(20),
            password_mode=True,
        )

        file_content = f"default_user = {username}\ndefault_pass = {password}"
        self.manager.add_variables(rabbitmq_username=username, rabbitmq_password=password)
        return file_content

    checker_class = KeysChecker


def configure():
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="Force fixing problematic files by rewriting them from scratch if any error is found. "
        "Be carefull to not use this command if you want to ensure you keep valueable "
        " settings written in the files located in the config folder.",
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Completely delete any previous configuration file. "
        "Be carrefull, this is a permanent data deletion operation and you "
        " can loose valueable settings written in the files located in the config folder.",
    )
    args = parser.parse_args()

    with InstallStatusRenderer(verbose=args.verbose) as renderer:

        installation = InstallationManager(renderer, fixmode=args.fix)
        installation.header()

        if args.delete:
            installation.delete_installation()

        installation.create_uploaded_folder()

        installation.setup_file(
            "db-secure-password",
            file_class=DbPasswordFile,
        ).setup_checker().make_install()

        django_source_file = installation.install_root_path / "docker" / "templates" / "custom_settings_template.py"
        installation.setup_file(
            "custom_settings.py",
            file_class=DjangoSettingsFile,
            source_file=django_source_file,
            replacements={
                "%SECRET_KEY%": installation.generate_password(),
                "%HOSTNAME%": gethostname(),
                "%TIMEZONE%": get_localzone().key,
            },
        ).setup_checker(pattern=r"^ *([A-Z_]+) *=", source_file=django_source_file).make_install()

        servers_json_source_file = installation.install_root_path / "docker" / "templates" / "servers.json"
        installation.setup_file(
            "servers.json",
            file_class=ServersJsonFile,
            source_file=servers_json_source_file,
            replacements={
                "%PG_USERNAME%": '"postgres"',
            },
        ).setup_checker(pattern=r"^ *([A-Z_]+) *:", source_file=servers_json_source_file).make_install()

        installation.setup_file("rabbitmq.conf", file_class=RabbitmqConfFile).setup_checker(
            keys={"default_user", "default_pass"}
        ).make_install()

        installation.setup_file("celery.env", file_class=CeleryEnvFile).setup_checker(
            keys={"RABBITMQ_USER", "RABBITMQ_PASSWORD", "FLOWER_USER", "FLOWER_PASSWORD"}
        ).make_install()

        installation.setup_file("pgadmin.env", file_class=PgadminEnvFile).setup_checker(
            keys={"PGADMIN_DEFAULT_EMAIL", "PGADMIN_DEFAULT_PASSWORD"}
        ).make_install()

        installation.report_status()
