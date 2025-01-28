from argparse import ArgumentParser
from socket import gethostname
from tzlocal import get_localzone
from .installation import Installation, InstallationUtilities
from .containers import Container
from .files import TemplatedFile


class DjangoServer(Container):
    container_name = "django_server"

    class DjangoSettingsFile(TemplatedFile):
        filename = "custom_settings.py"
        keywords = ["DJANGO_SECRET_KEY", "DB_BACKUP_HOSTNAME", "TIMEZONE", "MACHINE_ALLOWED_HOSTS"]

    class DjangoEntrypoint(TemplatedFile):
        filename = "entrypoint.sh"

    files_classes = [DjangoSettingsFile, DjangoEntrypoint]


class NginxServer(Container):
    container_name = "nginx_server"

    class NginxConfFile(TemplatedFile):
        filename = "nginx.conf"
        keywords = ["NGINX_OUT_PORT"]

    files_classes = [NginxConfFile]


class RabbitMQ(Container):
    container_name = "rabbitmq"

    class RabbitmqConfFile(TemplatedFile):
        filename = "rabbitmq.conf"
        keywords = ["RABBITMQ_USER", "RABBITMQ_PASSWORD"]

    files_classes = [RabbitmqConfFile]


class PostgresDB(Container):
    container_name = "postgres_db"

    class DbPasswordFile(TemplatedFile):
        filename = "db-secure-password"
        keywords = ["POSTGRES_DB_PASSWORD"]

    files_classes = [DbPasswordFile]


class PgAdmin(Container):
    container_name = "pgadmin"

    class ServersJsonFile(TemplatedFile):
        filename = "servers.json"
        keywords = ["POSTGRES_DB_USERNAME"]

    class PgadminEnvFile(TemplatedFile):
        filename = "pgadmin.env"
        keywords = ["PGADMIN_DEFAULT_EMAIL", "PGADMIN_DEFAULT_PASSWORD"]

    files_classes = [PgadminEnvFile, ServersJsonFile]


class CeleryServer(Container):
    container_name = "celery_server"

    class CeleryEnvFile(TemplatedFile):
        filename = "celery.env"
        keywords = ["RABBITMQ_USER", "RABBITMQ_PASSWORD"]

    files_classes = [CeleryEnvFile]


class ComposeEnvFile(TemplatedFile):
    filename = "compose.env"
    keywords = ["NGINX_RABBITMQ_PORT", "NGINX_OUT_PORT"]


class DockerInstallation(Installation, InstallationUtilities):
    # registers these containers for the installation
    containers_classes = [DjangoServer, NginxServer, PostgresDB, PgAdmin, RabbitMQ, CeleryServer]
    # registers these files (not linked to a specific container) for the installation
    files_classes = [ComposeEnvFile]

    def POSTGRES_DB_USERNAME(self):
        return "postgres"

    def POSTGRES_DB_PASSWORD(self):
        return self.renderer.ask(
            "Please enter a password for securing the postgresql database",
            self,
            default=self.generate_password(
                20, alphanum=True
            ),  # no special chars as they cause issues with the connection with pg_dumb through dbbackup
            password_mode=True,
        )

    def RABBITMQ_USER(self):
        username = self.renderer.ask(
            "Please enter an Username for securing the rabbitmq database",
            self,
            default="username",
        )
        return username

    def RABBITMQ_PASSWORD(self):
        password = self.renderer.ask(
            "Please enter a Password for securing the rabbitmq database",
            self,
            default=self.generate_password(20),
            password_mode=True,
        )
        return password

    def PGADMIN_DEFAULT_EMAIL(self):
        return "admin@admin.com"

    def PGADMIN_DEFAULT_PASSWORD(self):
        return self.renderer.ask(
            "Please enter a password for securing the pgadmin web interface",
            self,
            default=self.generate_password(20),
            password_mode=True,
        )

    def DJANGO_SECRET_KEY(self):
        return self.generate_password()

    def DB_BACKUP_HOSTNAME(self):
        return gethostname()

    def TIMEZONE(self):
        return get_localzone().key

    def MACHINE_ALLOWED_HOSTS(self):
        input_value = self.renderer.ask(
            "Please specify a port (example localhost, 127.0.0.1) that will be used to access the service from outside "
            "(usually you want to put the IP adress and / or network hostname of your machine in there) "
            "Must be comma separated.",
            self,
            default="localhost, 127.0.0.1",
            password_mode=False,
        )
        # input_value = "localhost, 127.0.0.1"  # make this the result of an ask request if necessary
        # validates that is has single quotes around each allowed hostname, and no space
        hosts = [f"'{host.replace(' ', '')}'" for host in input_value.split(",")]
        return ", ".join(hosts)

    def NGINX_OUT_PORT(self):
        return self.renderer.ask(
            "Please specify a port (only integers, like 80 , or 9876) that you will use to connect to the server.",
            self,
            default="80",
            password_mode=False,
        )

    def NGINX_RABBITMQ_PORT(self):
        return "5672"


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
    parser.add_argument(
        "--delete-noinput",
        action="store_true",
        help="Completely delete any previous configuration file, without asking for confirmation. "
        "Be carrefull, this is a permanent data deletion operation and you "
        " can loose valueable settings written in the files located in the config folder.",
    )
    parser.add_argument(
        "--noinput",
        action="store_true",
        help="Runs the configuration in no input mode, meaning that all operations that normally asks the user for "
        "an input will auto-complete, using default values for usernames and generated ones for passwords.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Runs the configuration asking every information that can be entered, again.",
    )
    parser.add_argument(
        "--inputs-only", action="store_true", help="Makes the configuration input_fields.json file only."
    )
    parser.add_argument("-t", "--test", action="store_true")
    args = parser.parse_args()

    with DockerInstallation.from_arguments(args) as installation:
        if installation.delete:
            installation.delete_configuration()
        installation.install()
        installation.create_data_folder()
