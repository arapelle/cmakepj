import pathlib
import re


class CMakeListsFile:
    def __init__(self, contents=""):
        self.__file_path = None
        self._contents = contents

    @property
    def file_path(self):
        return self.file_path

    @property
    def contents(self):
        return self._contents

    def load(self, file_path):
        if not pathlib.Path(file_path).exists():
            raise ValueError(file_path)
        self.__file_path = file_path
        with open(self.__file_path, "r", newline='\n') as file:
            self._contents = file.read()

    def save(self, file_path=None):
        if file_path is None:
            file_path = self.__file_path
        else:
            self.__file_path = file_path
        with open(file_path, "w", newline='\n') as file:
            file.write(self._contents)

    def update_dependency_version(self, dependency_name, current_version, new_version):
        regex = CMakeListsFile.__find_dependency(dependency_name, current_version)
        match: re.Match = regex.search(self._contents)
        if match is not None:
            self._contents = self._contents.replace(match.group(0),
                                                    self.__format_dependency(dependency_name, new_version))

    @staticmethod
    def __format_dependency(dependency_name, version):
        return f"find_package({dependency_name} {version}"

    @staticmethod
    def __find_dependency(dependency_name, current_version):
        version_regex = re.compile(r"find_package\(\s*" + dependency_name + r"\s+" + current_version)
        return version_regex
