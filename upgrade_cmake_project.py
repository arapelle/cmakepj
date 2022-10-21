#!/usr/bin/env python
import glob
import os
import pathlib
import re
from copy import deepcopy
from enum import Enum, IntEnum

import git.config
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
            raise Exception("ERROR - Project name not found.")
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


class CMakeProject:
    def __init__(self, repository_path):
        print(f"INFO - Load git repository.")
        self.__git = git.Git = git.Git(git.Git.GIT_PYTHON_GIT_EXECUTABLE)
        self.__repository = Repo(repository_path)
        print(f"INFO - Load project CMakeLists.txt.")
        self.__project_cmakelists_file = ProjectCMakeListsFile(f"{repository_path}/CMakeLists.txt")

    def project_name(self):
        return self.__project_cmakelists_file.project_name

    def project_version(self):
        return self.__project_cmakelists_file.project_version

    def upgrade_project_version(self, release_comp: ReleaseComponent, commit=True):
        print(f"INFO - Upgrade project {release_comp.name} version.")
        old_project_version = self.__project_cmakelists_file.project_version
        self.__project_cmakelists_file.upgrade_project_version(release_comp)
        new_project_version = self.__project_cmakelists_file.project_version
        self.__project_cmakelists_file.save()
        self.update_dependency_version(self.__project_cmakelists_file.project_name,
                                       old_project_version, new_project_version)
        if commit:
            self.commit_start_version()

    def update_dependency_version(self, dependency_name, old_version, new_version):
        print(f"INFO - Update dependency '{dependency_name}' from version {old_version} to {new_version}.")
        cmakelists_files = glob.glob("**/CMakeLists.txt", recursive=True)
        for cmakelists_file_path in cmakelists_files:
            cmakelists_file = CMakeListsFile()
            cmakelists_file.load(cmakelists_file_path)
            cmakelists_file.update_dependency_version(dependency_name, old_version, new_version)
            cmakelists_file.save()

    def checkout_develop_branch(self, branch='develop'):
        print(f"INFO - Checkout {branch}.")
        self.__repository.git.checkout(f'{branch}')

    def commit_start_version(self):
        version = self.project_version()
        print(f"INFO - Commit start version {version}.")
        files = [item.a_path for item in self.__repository.index.diff(None)]
        self.__repository.index.add(files)
        commit_msg = f"v{version}: Start version {version}."
        self.__repository.index.commit(commit_msg)

    def set_submodule_branch(self, submodule_name, branch, commit=True):
        print(f"INFO - Set submodule branch {submodule_name}.branch = {branch}.")
        submodule = self.__repository.submodule(submodule_name)
        cf_writer: git.config.SectionConstraint = submodule.config_writer()
        cf_writer.set_value('branch', branch).release()
        self.__git.execute("git submodule update --remote".split())
        if commit:
            print(f"INFO - Commit submodule branch changes.")
            self.__git.execute(f"git add {submodule.path}".split())
            commit_msg = f"v{self.project_version()}: Use {submodule.name} {branch}."
            self.__repository.index.commit(commit_msg)


cmake_project = CMakeProject(".")
print(f"INFO - CMake project {cmake_project.project_name()} {cmake_project.project_version()}")
cmake_project.checkout_develop_branch()
cmake_project.upgrade_project_version(ReleaseComponent.MINOR)
cmake_project.set_submodule_branch('cmake/cmtk', 'release/0.6')

print('EXIT SUCCESS')
