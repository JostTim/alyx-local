from pathlib import Path
import shutil
from re import match
from typing import List, Type, Optional, Dict, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    from .installation import Installation
    from .files import File


class Container:

    files_classes: "List[Type[File]]"
    path_suffix: Path | str
    container_name: str

    def __init__(self, manager: "Installation", container_name: Optional[str] = None):
        """Initialize an instance of the class.

        Args:
            manager (Installation): An instance of the Installation manager.
            container_name (Optional[str], optional): The name of the container.
                If not provided, must be set later. Defaults to None.

        Raises:
            ValueError: If container_name is not provided and cannot be resolved.
        """

        self.manager = manager
        self.renderer = manager.renderer
        if container_name:
            self.container_name = container_name
        elif not hasattr(self, "container_name"):
            raise ValueError("Cannot resolve the container name")

    @property
    def destination_path(self):
        """Returns the destination path based on the object's attributes.

        This method constructs a destination path by checking if the object has a
        `path_suffix` attribute. If `path_suffix` is not present, it returns a path
        composed of the manager's `config_path` and the object's `container_name`.
        If `path_suffix` exists, it returns a path composed of the manager's
        `config_path` and the `path_suffix`.

        Returns:
            Path: The constructed destination path.
        """
        if not hasattr(self, "path_suffix"):
            return self.manager.config_path / self.container_name
        return self.manager.config_path / self.path_suffix

    @property
    def source_path(self):
        """Returns the source path for the container.

        This method constructs the source path based on the presence of the
        `path_suffix` attribute. If `path_suffix` is not set, it returns the
        default path using the container's name. Otherwise, it returns the
        path using the specified `path_suffix`.

        Returns:
            Path: The constructed source path for the container.
        """
        if not hasattr(self, "path_suffix"):
            return self.manager.docker_path / self.container_name
        return self.manager.docker_path / self.path_suffix

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
        """Install all files.

        This method iterates over the list of files and calls the install method on each file.

        Attributes:
            files (list): A list of file objects that have an install method.

        Returns:
            None
        """

        for file in self.files:
            file.install()
        self.copy_dockerfile()

    def copy_dockerfile(self):
        """Copies the Dockerfile from the source path to the destination path if it is not managed by any file class.

        This method checks if the Dockerfile exists in the specified path and if it is not already managed
        by any of the files. If both conditions are met, it copies the Dockerfile from
        the source directory to the destination directory and prints a confirmation message.

        Attributes:
            dockerfile_path (Path): The path of the Dockerfile to be copied.
            source_path (Path): The source directory where the Dockerfile is located.
            destination_path (Path): The destination directory where the Dockerfile should be copied.
            files (list): A list of file objects that may manage the Dockerfile.
            renderer (object): An object responsible for rendering output messages.

        Returns:
            None
        """
        # is a dockerfile definition is not present in the compose.yaml file, then there is no file to copy
        if not self.dockerfile_path:
            return

        # If any file class is responsible for managing the dockerfile,
        # then we don't interfere and let the role of copying and editing it to that class
        if any([file.filename == self.dockerfile_path.name for file in self.files]):
            return

        docker_source = (self.source_path / self.dockerfile_path).resolve()
        docker_destination = (self.destination_path / self.dockerfile_path).resolve()

        self.renderer.title(f"{self.container_name}/{self.dockerfile_path}")

        if docker_destination.is_file():
            with open(docker_source, "r") as source, open(docker_destination, "r") as destination:
                source_content = source.read()
                destination_content = destination.read()
            if source_content == destination_content:
                self.renderer.success("All good")
                return
            else:
                self.renderer.print(
                    f"The master dockerfile for {self.container_name} has some difference with the actual one. "
                    "Overwriting."
                )

        shutil.copy2(docker_source, docker_destination)
        self.renderer.success(f"The dockerfile {self.dockerfile_path} has been copied to config folder.")

    @property
    def dockerfile_path(self) -> Path | None:
        """Returns the path to the Dockerfile if it exists, otherwise returns None.

        This method checks if the instance has a Dockerfile attribute. If the attribute exists,
        it returns its path; otherwise, it returns None.

        Returns:
            Path | None: The path to the Dockerfile or None if it does not exist.
        """
        if not hasattr(self, "_dockerfile_path"):
            for line in self.config:
                if result := match("^ *dockerfile *: *(.*?)$", line):
                    self._dockerfile_path = Path(result.group(1).replace("./config/", ""))
                    if str(self._dockerfile_path.parent) == self.container_name:
                        self._dockerfile_path = Path(self._dockerfile_path.name)
                    break
            else:
                self._dockerfile_path = None
        return self._dockerfile_path

    @property
    def config(self) -> List[str]:
        """Retrieve the configuration for the instance. If the configuration has not been
        previously set, it will be generated using the `_get_compose_config` method.

        Returns:
            dict: The configuration dictionary for the instance.
        """
        if not hasattr(self, "_config"):
            self._config = self._get_compose_config()
        return self._config

    def _get_compose_config(self) -> List[str]:
        """Retrieves the configuration section for a specified container from a Docker Compose file.

        This function reads the Docker Compose configuration file, identifies the section corresponding to the
        specified container name, and returns the relevant lines of configuration.

        Returns:
            List[str]: A list of strings representing the lines of configuration for the specified container.

        Raises:
            ValueError: If the section start or end cannot be identified, or if multiple definitions are found
            for the container.
        """

        def get_indentation(line: str):
            """Calculates the number of leading spaces (indentation) in a given line of text.

            Args:
                line (str): The line of text from which to calculate the indentation.

            Returns:
                int: The number of leading spaces in the line.
            """
            return len(line) - len(line.lstrip(" "))

        def get_section_limits(section_start_line: int):
            """Get the limits of a section in a configuration file.

            This function identifies the start and end lines of a section based on the
            indentation level of the lines in the configuration content. It takes the
            starting line of the section as input and returns a tuple containing the
            start and stop line numbers.

            Args:
                section_start_line (int): The line number where the section starts.

            Returns:
                tuple: A tuple containing the start and stop line numbers of the section.

            Raises:
                ValueError: If the end of the section cannot be identified.
            """
            definition_line = config_content[section_start_line]
            section_indentation = get_indentation(definition_line)
            for line_number, line in enumerate(config_content[section_start_line + 1 :]):
                if get_indentation(line) <= section_indentation and line.lstrip(" "):
                    start = section_start_line
                    stop = section_start_line + line_number
                    self.renderer.comment(f"start={config_content[start]}, stop={config_content[stop]}")
                    return (start, stop)
            raise ValueError(f"Could not identify the section end for container {self.container_name}")

        def get_section_start(section_name_line: int):
            """Get the starting line number of a section in a configuration file.

            Args:
                section_name_line (int): The line number where the section name is defined.

            Returns:
                int: The line number of the start of the section.

            Raises:
                ValueError: If the section start cannot be identified.

            This function searches for the first line above the specified section name line
            that has less indentation, indicating the start of the section.
            """
            definition_line = config_content[section_name_line]
            name_indentation = get_indentation(definition_line)
            for line_number, line in enumerate(config_content[section_name_line - 1 : 0 : -1]):
                if get_indentation(line) < name_indentation and line.lstrip(" "):
                    return section_name_line - 1 - line_number
            raise ValueError(f"Could not identify the section start for container {self.container_name}")

        def find_definitions() -> List[Dict[str, int]]:
            """Finds the definitions of a specified container in the configuration content.

            This function searches through the `config_content` for lines that match the specified
            container name. It identifies both the container name and the container section,
            recording their line numbers.

            Returns:
                List[Dict[str, int]]: A list of dictionaries where each dictionary contains
                the type of definition found (either 'container_name' or 'container_section')
                as the key and the corresponding line number as the value.

            Example:
                If the container name is 'my_container', and it is found on line 5 and
                the section starts on line 10, the return value would be:
                [{'container_name': 5}, {'container_section': 10}]
            """
            container_definition = []

            for line_number, line in enumerate(config_content):
                if match(f"^ *container_name *: *(?:'|\")?{self.container_name}(?:'|\")? *$", line):
                    self.renderer.comment(f"container_name n°{line_number}-{line}")
                    container_definition.append({"container_name": line_number})
                elif match(f"^ *{self.container_name}: *$", line):
                    self.renderer.comment(f"container_section n°{line_number}-{line}")
                    container_definition.append({"container_section": line_number})

            return container_definition

        def find_section_limits() -> Tuple[int, int]:
            """Finds the section limits for a container defined in a YAML file.

            This function iterates through container definitions to identify the start and end line numbers of
            sections related to a specific container. It raises an error if no valid definitions are found
            or if multiple definitions are detected.

            Returns:
                Tuple[int, int]: A tuple containing the start and end line numbers of the container section.

            Raises:
                ValueError: If no valid definition is found for the container or if multiple definitions are found.
            """
            container_limits: List[Tuple[int, int]] = []

            for definition in container_definition:
                definition_type = list(definition.keys())[0]
                definition_line_number = list(definition.values())[0]

                if definition_type == "container_section":
                    container_limits.append(get_section_limits(definition_line_number))

                if definition_type == "container_name":
                    section_start = get_section_start(definition_line_number)
                    self.renderer.comment(f"section_start={section_start}")
                    container_limits.append(get_section_limits(section_start))

            limits = set(container_limits)
            if not limits:
                raise ValueError(f"Cannot find valid definition in compose.yaml for container {self.container_name} ! ")
            if len(limits) > 1:
                raise ValueError(
                    f"Several definitions are found for the container {self.container_name}: "
                    f"{[f'Line {limit[0] + 1} to line {limit[1] + 1}' for limit in limits]}"
                )
            return list(limits)[0]

        with open(self.manager.compose_path, "r") as f:
            config_content = f.read().splitlines()

        container_definition = find_definitions()
        limits = find_section_limits()

        return config_content[slice(*limits)]
