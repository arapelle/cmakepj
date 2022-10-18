#!/usr/bin/env python
import glob
import os
import pathlib
import re
from copy import deepcopy
from enum import Enum, IntEnum

import packaging.version
from packaging.version import Version, parse
from git import Repo


class ReleaseComponent(IntEnum):
    MAJOR = 0,
    MINOR = 1,
    PATCH = 2


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

    def update_dependency_version(self, current_version, new_version):
        fp_version_regex = CMakeListsFile.__find_package_version_regex(current_version)
        fp_version_match: re.Match = fp_version_regex.search(self._contents)
        if fp_version_match is not None:
            print(f"    matching. converting to new_version: {new_version}")
#           contents.replace()

    @staticmethod
    def __find_package_version_regex(current_version):
        print(f"current_version: {current_version}")
        version_regex = re.compile(r"find_package\(([^\s]+\s+)" + current_version + r"(\s+.*\#project-version)",
                                      re.VERBOSE | re.IGNORECASE)
        return version_regex


class ProjectCMakeListsFile(CMakeListsFile):
    def __init__(self, file_path):
        super(ProjectCMakeListsFile, self).__init__()
        self.__project_version = None
        self.load(file_path)

    def load(self, file_path):
        super().load(file_path)
        # self.__project_name = ...
        # self.__package_name = ...
        # self.__project_full_version = ...
        self.__project_version = self.__find_project_version()

    @property
    def project_version(self):
        return self.__project_version

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
            raise Exception("ERROR - Project version not found.")
        return pr_version_match

    def upgraded_version(self, release_comp: ReleaseComponent):
        ver = Version(self.__project_version)
        epoch = ver.epoch
        v_release = list(ver.release)
        v_release[release_comp] += 1
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
    def __format_project_version_declaration(project_version):
        return f"VERSION {project_version} #project-version"

    @staticmethod
    def __project_version_regex():
        pr_version_regex = re.compile(r"VERSION\s+(" + packaging.version.VERSION_PATTERN + r")\s*\#project-version",
                                      re.VERBOSE | re.IGNORECASE)
        return pr_version_regex


class CMakeProject:
    def __init__(self, repository_path):
        self.__repository = Repo(repository_path)
        self.__project_cmakelists_file = ProjectCMakeListsFile(f"{repository_path}/CMakeLists.txt")

    def upgrade(self, release_comp: ReleaseComponent):
        old_project_version = self.__project_cmakelists_file.project_version
        self.__project_cmakelists_file.upgrade_project_version(release_comp)
        new_project_version = self.__project_cmakelists_file.project_version
        self.__project_cmakelists_file.save()
        cmakelists_files = glob.glob("**/CMakeLists.txt", recursive=True)
        for cmakelists_file_path in cmakelists_files:
            print(f"  Treating file '{cmakelists_file_path}'")
            cmakelists_file = CMakeListsFile()
            cmakelists_file.load(cmakelists_file_path)
            cmakelists_file.update_dependency_version(old_project_version, new_project_version)

    def checkout_develop_branch(self, branch):
        print(f"INFO - Checkout {branch}")
        self.__repository.git.checkout(f'{branch}')

    def commit_start_version(self, new_project_version):
        print("INFO - Add CMakeLists.txt to index")
        self.__repository.index.add(["CMakeLists.txt"])
        print("INFO - Commit")
        self.__repository.index.commit(f"v{new_project_version}: Start version {new_project_version}.")


cmake_project = CMakeProject(".")
cmake_project.upgrade(ReleaseComponent.MINOR)

print('EXIT SUCCESS')
