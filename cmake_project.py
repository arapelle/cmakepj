import glob
import re

import git.config
import packaging.version
from git import Repo

from cmakelists_file import CMakeListsFile
from project_cmakelists_file import ProjectCMakeListsFile
from release_component import ReleaseComponent


class CMakeProject:
    def __init__(self, repository_path):
        print(f"INFO - Load git repository.")
        self.__repository = Repo(repository_path)
        self.__git = git.Git = self.__repository.git
        print(f"INFO - Load project CMakeLists.txt.")
        self.__project_cmakelists_file = ProjectCMakeListsFile(f"{repository_path}/CMakeLists.txt")
        print(f"INFO - CMake project {self.project_name()} {self.project_version()}")

    def git_repository(self):
        return self.__repository

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
        self.upgrade_dependency_version(self.__project_cmakelists_file.project_name,
                                        old_project_version, new_project_version)
        if commit:
            self.commit_start_version()

    def upgrade_dependency_version(self, dependency_name, old_version, new_version):
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

    def upgrade_submodule_branch_to_last_release(self, submodule_name, commit=True):
        print(f"INFO - Upgrade submodule branch {submodule_name} to last release.")
        submodule = self.__repository.submodule(submodule_name)
        last_release_branch = self.last_release_branch(submodule.url)
        self.set_submodule_branch(submodule_name, last_release_branch[1], commit)

    def last_release_branch(self, repository_url, release_prefix="release/"):
        repo_info = self.__git.execute(f"git ls-remote {repository_url}".split())
        repo_lines = repo_info.splitlines()
        release_tag_regex = re.compile("refs/tags/([^{]*)$")
        release_branch_regex = re.compile("refs/heads/(" + release_prefix + "[^{]*)$")
        tag_versions = []
        for repo_line in repo_lines:
            match = release_tag_regex.search(str(repo_line))
            if match:
                tag_match = match.group(1)
                tag_version = self.__find_version_in_str(tag_match)
                if tag_version:
                    tag_versions.append(tag_version)
        release_branches = dict()
        for repo_line in repo_lines:
            match = release_branch_regex.search(str(repo_line))
            if match:
                branch_name = match.group(1)
                branch_version = self.__find_version_in_str(branch_name)
                if branch_version and branch_version in tag_versions:
                    release_branches[branch_version] = branch_name
        print(release_branches)
        return list(release_branches.items())[-1] if len(release_branches) > 0 else None

    @staticmethod
    def __find_version_in_str(input_str: str):
        version_regex = re.compile(r"(" + packaging.version.VERSION_PATTERN + r")", re.VERBOSE | re.IGNORECASE)
        match = version_regex.search(input_str)
        if match:
            return match.group(1)
        return None

    def start_release(self):
        version = self.project_version()
        print(f"INFO - Start release release/{version}.")
        self.__repository.git.execute(f"git flow release start {version}".split())
        self.__repository.git.execute(f"git flow release publish {version}".split())
        self.__repository.git.push(self.__repository.remote().name, self.__repository.active_branch.name)

    def finish_release(self):
        version = self.project_version()
        print(f"INFO - Finish release release/{version}.")
        # To get git-flow argument list: git flow release finish -h
        gf_cmd = []
        gf_cmd.extend("git flow release finish".split())
        gf_cmd.append(f"-m'Tag {version}'")
        gf_cmd.extend(f"--pushproduction --pushdevelop --pushtag --keepremote --nokeeplocal --nodevelopmerge".split())
        gf_cmd.append(f"'{version}'")
        self.__repository.git.execute(gf_cmd)
        self.checkout_develop_branch()

    def create_release(self):
        self.start_release()
        self.finish_release()
