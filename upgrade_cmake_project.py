#!/usr/bin/env python
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

    def upgrade_project_version(self, release_comp: ReleaseComponent):
        print("INFO - Upgrade project version")
        # Version Identification and Dependency Specification: https://peps.python.org/pep-0440/
        with open("CMakeLists.txt", "r", newline='\n') as file:
            contents = file.read()
        pr_version_regex = re.compile(r"VERSION\s+(" + packaging.version.VERSION_PATTERN + r")\s*\#project-version",
                                      re.VERBOSE | re.IGNORECASE)
        # contents = "VERSION 2022!1.2.3.4rc0.dev44+nike.1.2 #project-version"
        pr_version_match: re.Match = pr_version_regex.search(contents)
        if pr_version_match is None:
            raise Exception("ERROR - Project version not found.")
        print(pr_version_match)
        matching_str = pr_version_match.group(0)
        print(f"'{matching_str}'")
        project_version = pr_version_match.group(1)
        new_project_version = self.upgraded_version(project_version, release_comp)
        new_str = f"VERSION {new_project_version} #project-version"
        contents = contents.replace(matching_str, new_str)
        with open("CMakeLists.txt", "w", newline='\n') as file:
            file.write(contents)
        return new_project_version

    def checkout_develop_branch(self, branch):
        print(f"INFO - Checkout {branch}")
        self.__repository.git.checkout(f'{branch}')

    def commit_start_version(self, new_project_version):
        print("INFO - Add CMakeLists.txt to index")
        self.__repository.index.add(["CMakeLists.txt"])
        print("INFO - Commit")
        self.__repository.index.commit(f"v{new_project_version}: Start version {new_project_version}.")


upgrader = CMakeProjectUpgrader(".")
upgrader.checkout_develop_branch("develop")
new_project_version = upgrader.upgrade_project_version(ReleaseComponent.MINOR)
upgrader.commit_start_version(new_project_version)

print('EXIT SUCCESS')
