#!/usr/bin/env python
import re

import packaging.version
from packaging.version import Version, parse
from git import Repo


class CMakeProjectUpgrader():
    def compute_upgraded_version(self, ver_str: str):
        ver = Version(ver_str)
        print(f"input: {ver_str}")
        # print(f"public: {ver.public}")
        # print(f"epoch: {ver.epoch}")
        # print(f"base: {ver.base_version}")
        # print(f"release: {ver.release}")
        # print(f"pre: {ver.is_prerelease} {ver.pre}")
        # print(f"post: {ver.is_postrelease} {ver.post}")
        # print(f"dev: {ver.is_devrelease} {ver.dev}")
        # print(f"local: '{ver.local}'")
        # print(f"output: '{ver.public}{'+'+ver.local if ver.local else ''}'")
        epoch = ver.epoch
        v_release = list(ver.release)
        v_release[1] += 1
        release_segment = ".".join(str(x) for x in v_release)
        pre = "".join(str(x) for x in ver.pre) if ver.is_prerelease else ''
        post = f".post{ver.post}" if ver.is_postrelease else ''
        dev = f".dev{ver.dev}" if ver.is_devrelease else ''
        local = f"+{ver.local}" if ver.local else ''
        upgrade = f"{epoch}!{release_segment}{pre}{post}{dev}{local}"
        print(f"upgrade str: '{upgrade}'")
        new_ver = str(Version(upgrade))
        print(f"upgrade: '{new_ver}'")
        print('-' * 100)
        return new_ver


    def upgrade_project_version(self):
        # Version Identification and Dependency Specification: https://peps.python.org/pep-0440/
        with open("CMakeLists.txt", "r", newline='\n') as file:
            contents = file.read()
        pr_version_regex = re.compile(r"VERSION\s+(" + packaging.version.VERSION_PATTERN + r")\s*\#project-version",
                                      re.VERBOSE | re.IGNORECASE)
        # contents = "VERSION 2022!1.2.3.4rc0.dev44+nike.1.2 #project-version"
        # pr_version_match: re.Match = pr_version_regex.search(contents)
        # print(f"'{pr_version_match.group(0)}'")
        # pr_version: Version = parse(pr_version_match.group(1))
        # print_version(str(pr_version))
        pr_version_match: re.Match = pr_version_regex.search(contents)
        print(pr_version_match)
        matching_str = pr_version_match.group(0)
        print(f"'{matching_str}'")
        project_version = pr_version_match.group(1)
        new_project_version = self.compute_upgraded_version(project_version)
        new_str = f"VERSION {new_project_version} #project-version"
        contents = contents.replace(matching_str, new_str)
        with open("CMakeLists.txt", "w", newline='\n') as file:
            file.write(contents)
        return new_project_version


    def run(self):
        print("INFO - Load repository")
        repo = Repo('.')
        print("INFO - Checkout develop")
        repo.git.checkout('develop')
        print("INFO - Upgrade project version")
        new_project_version = self.upgrade_project_version()
        print("INFO - Add CMakeLists.txt to index")
        repo.index.add(["CMakeLists.txt"])
        print("INFO - Commit")
        repo.index.commit(f"v{new_project_version}: Start version {new_project_version}.")


upgrader = CMakeProjectUpgrader()
upgrader.run()
print('EXIT SUCCESS')
