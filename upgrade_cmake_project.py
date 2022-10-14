#!/usr/bin/env python
import glob
import os
import re
from enum import Enum, IntEnum

import packaging.version
from packaging.version import Version, parse
from git import Repo


class ReleaseComponent(IntEnum):
    MAJOR = 0,
    MINOR = 1,
    PATCH = 2


class CMakeProjectUpgrader:
    def __init__(self, repository_path):
        self.__repository = Repo(repository_path)

    def upgraded_version(self, ver_str: str, release_comp: ReleaseComponent):
        ver = Version(ver_str)
        epoch = ver.epoch
        v_release = list(ver.release)
        v_release[release_comp] += 1
        release_segment = ".".join(str(x) for x in v_release)
        pre = "".join(str(x) for x in ver.pre) if ver.is_prerelease else ''
        post = f".post{ver.post}" if ver.is_postrelease else ''
        dev = f".dev{ver.dev}" if ver.is_devrelease else ''
        local = f"+{ver.local}" if ver.local else ''
        upgrade = f"{epoch}!{release_segment}{pre}{post}{dev}{local}"
        new_ver = str(Version(upgrade))
        return new_ver

    def upgrade_version_in_project_cmakelists_txt(self, release_comp: ReleaseComponent):
        print("INFO - Upgrade project version")
        # Version Identification and Dependency Specification: https://peps.python.org/pep-0440/
        # contents = "VERSION 2022!1.2.3.4rc0.dev44+nike.1.2 #project-version"
        with open("CMakeLists.txt", "r", newline='\n') as file:
            contents = file.read()
        pr_version_regex = self.__project_version_regex()
        pr_version_match: re.Match = pr_version_regex.search(contents)
        if pr_version_match is None:
            raise Exception("ERROR - Project version not found.")
        matching_str = pr_version_match.group(0)
        project_version = pr_version_match.group(1)
        print(f"matching_str: {matching_str}")
        print(f"project_version: {project_version}")
        new_project_version = self.upgraded_version(project_version, release_comp)
        new_str = f"VERSION {new_project_version} #project-version"
        contents = contents.replace(matching_str, new_str)
        # with open("CMakeLists.txt", "w", newline='\n') as file:
        #     file.write(contents)
        return project_version, new_project_version

    def __project_version_regex(self):
        pr_version_regex = re.compile(r"VERSION\s+(" + packaging.version.VERSION_PATTERN + r")\s*\#project-version",
                                      re.VERBOSE | re.IGNORECASE)
        return pr_version_regex

    def upgrade_version_in_examples_cmakelists_txt(self, current_version, new_version):
        print("INFO - Upgrade other project files")
        fp_version_regex = self.__find_package_version_regex(current_version)
        cmakelists_files = glob.glob("**/CMakeLists.txt", recursive=True)
        for cmakelists_file in cmakelists_files:
            print(f"  Treating file '{cmakelists_file}'")
            with open(cmakelists_file, "r", newline='\n') as file:
                contents = file.read()
                fp_version_match: re.Match = fp_version_regex.search(contents)
                if fp_version_match is None:
                    continue
                print("    matching")
#                contents.replace()
        pass

    def __find_package_version_regex(self, current_version):
        print(f"current_version: {current_version}")
        version_regex = re.compile(r"find_package\(([^\s]+\s+)" + current_version + r"(\s+.*\#project-version)",
                                      re.VERBOSE | re.IGNORECASE)
        return version_regex

    def checkout_develop_branch(self, branch):
        print(f"INFO - Checkout {branch}")
        self.__repository.git.checkout(f'{branch}')

    def commit_start_version(self, new_project_version):
        print("INFO - Add CMakeLists.txt to index")
        self.__repository.index.add(["CMakeLists.txt"])
        print("INFO - Commit")
        self.__repository.index.commit(f"v{new_project_version}: Start version {new_project_version}.")


upgrader = CMakeProjectUpgrader(".")
# upgrader.checkout_develop_branch("develop")
project_version, new_project_version = upgrader.upgrade_version_in_project_cmakelists_txt(ReleaseComponent.MINOR)
upgrader.upgrade_version_in_examples_cmakelists_txt(project_version, new_project_version)
# upgrader.commit_start_version(new_project_version)

print('EXIT SUCCESS')
