import re

import packaging.version
from packaging.version import Version

from cmakelists_file import CMakeListsFile
from release_component import ReleaseComponent


class ProjectCMakeListsFile(CMakeListsFile):
    def __init__(self, file_path):
        super(ProjectCMakeListsFile, self).__init__()
        self.__project_name = None
        self.__project_version = None
        self.load(file_path)

    def load(self, file_path):
        super().load(file_path)
        self.__project_name = self.__find_project_name()
        # self.__package_name = ...
        # self.__project_full_version = ...
        self.__project_version = self.__find_project_version()

    @property
    def project_name(self):
        return self.__project_name

    @property
    def project_version(self):
        return self.__project_version

    def __find_project_name(self):
        regex = ProjectCMakeListsFile.__project_name_regex()
        match: re.Match = regex.search(self._contents)
        if match is None:
            raise Exception("ERROR - Project name: set(PROJECT_NAME \"...\") is missing.")
        return match.group(1)

    def __find_project_version(self):
        pr_version_match = self.__find_project_version_match()
        return pr_version_match.group(1)

    def __find_project_version_declaration(self):
        pr_version_match = self.__find_project_version_match()
        return pr_version_match.group(0)

    def __find_project_version_match(self):
        pr_version_regex = ProjectCMakeListsFile.__project_version_regex()
        pr_version_match: re.Match = pr_version_regex.search(self._contents)
        if pr_version_match is None:
            raise Exception("ERROR - Project version: set(PROJECT_VERSION \"...\") is missing.")
        return pr_version_match

    def upgraded_version(self, release_comp: ReleaseComponent):
        ver = Version(self.__project_version)
        epoch = ver.epoch
        v_release = list(ver.release)
        v_release[release_comp] += 1
        for i in range(int(release_comp) + 1, len(v_release)):
            v_release[i] = 0
        release_segment = ".".join(str(x) for x in v_release)
        pre = "".join(str(x) for x in ver.pre) if ver.is_prerelease else ''
        post = f".post{ver.post}" if ver.is_postrelease else ''
        dev = f".dev{ver.dev}" if ver.is_devrelease else ''
        local = f"+{ver.local}" if ver.local else ''
        upgrade = f"{epoch}!{release_segment}{pre}{post}{dev}{local}"
        new_version = str(Version(upgrade))
        return new_version

    def upgrade_project_version(self, release_comp: ReleaseComponent):
        self.__project_version = self.upgraded_version(release_comp)
        new_pj_version_declaration = self.__format_project_version_declaration(self.__project_version)
        self._contents = self._contents.replace(self.__find_project_version_declaration(), new_pj_version_declaration)

    @staticmethod
    def __format_project_name_declaration(project_name):
        return f"set(PROJECT_NAME {project_name})"

    @staticmethod
    def __format_project_version_declaration(project_version):
        return f"set(PROJECT_VERSION {project_version})"

    @staticmethod
    def __project_name_regex():
        return re.compile(r"set\(PROJECT_NAME\s+([^\s]+)\s*\)")

    @staticmethod
    def __project_version_regex():
        return re.compile(r"set\(PROJECT_VERSION\s+(" + packaging.version.VERSION_PATTERN + r")\s*\)",
                          re.VERBOSE | re.IGNORECASE)
