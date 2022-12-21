#!/usr/bin/env python
import argparse

from cl_command import CLCommand
from cmake_project import CMakeProject
from release_component import ReleaseComponent


class Cmakepj(CLCommand):
    def __init__(self):
        super().__init__()
        self.arg_parser = argparse.ArgumentParser(self.class_name_label())
        subparsers = self.arg_parser.add_subparsers(dest=self.subcommand_label(), required=True)
        self.version = self.Version(subparsers)
        self.release = self.Release(subparsers)
        self.submodule = self.Submodule(subparsers)

    class Version(CLCommand):
        def __init__(self, subparsers):
            super().__init__()
            self.arg_parser = subparsers.add_parser(self.class_name_label())
            subparsers = self.arg_parser.add_subparsers(dest=self.subcommand_label(), required=True)
            self.add_set_parser(subparsers)
            self.add_up_parser(subparsers)

        def add_set_parser(self, subparsers):
            parser: argparse.ArgumentParser = subparsers.add_parser("set")
            parser.add_argument("version")
            parser.add_argument("-c", "--commit", action="store_true")
            parser.add_argument("-p", "--push", action="store_true")

        def add_up_parser(self, subparsers):
            parser: argparse.ArgumentParser = subparsers.add_parser("up")
            parser.add_argument("release_component", choices=["major", "minor", "patch"])
            parser.add_argument("-c", "--commit", action="store_true")
            parser.add_argument("-p", "--push", action="store_true")

        def set(self, args):
            print(args)
            pass

        def up(self, args):
            cmake_project = CMakeProject(".")
            rcomp = args.release_component.upper()
            rcomp = ReleaseComponent[rcomp]
            cmake_project.upgrade_project_version(rcomp, args.commit)

    class Release(CLCommand):
        def __init__(self, subparsers):
            super().__init__()
            self.arg_parser: argparse.ArgumentParser = subparsers.add_parser(self.class_name_label())
            self.arg_parser.add_argument(self.subcommand_label(), choices=["start", "finish", "create"])

        def start(self, args):
            cmake_project = CMakeProject(".")
            cmake_project.start_release()

        def finish(self, args):
            cmake_project = CMakeProject(".")
            cmake_project.finish_release()

        def create(self, args):
            self.start(args)
            self.finish(args)

    class Submodule(CLCommand):
        def __init__(self, subparsers):
            super().__init__()
            self.__set_branch_parser = None
            self.arg_parser = subparsers.add_parser(self.class_name_label())
            subparsers = self.arg_parser.add_subparsers(dest=self.subcommand_label(), required=True)
            self.add_set_branch_parser(subparsers)

        def add_set_branch_parser(self, subparsers):
            self.__set_branch_parser = subparsers.add_parser("set-branch")
            self.__set_branch_parser.add_argument("module")
            self.__set_branch_parser.add_argument("branch", nargs='?')
            self.__set_branch_parser.add_argument("-l", "--last", action="store_true")
            self.__set_branch_parser.add_argument("-c", "--commit", action="store_true")
            self.__set_branch_parser.add_argument("-p", "--push", action="store_true")

        def set_branch(self, args):
            cmake_project = CMakeProject(".")
            if args.last:
                if args.branch:
                    self.__set_branch_parser.print_help()
                    print(f"\nerror: -l, --last option is provided, so branch ({args.branch}) argument is not needed.")
                    exit(-1)
                else:
                    cmake_project.upgrade_submodule_branch_to_last_release(args.module, args.commit)
            elif args.branch is None:
                self.__set_branch_parser.print_help()
                print(f"\nerror: branch argument is required when -l option is not provided.")
                exit(-1)
            else:
                cmake_project.set_submodule_branch(args.module, args.branch, args.commit)

    class Dependency(CLCommand):
        def __init__(self, subparsers):
            super().__init__()
            self.__upgrade_parser = None
            self.arg_parser = subparsers.add_parser(self.class_name_label())
            subparsers = self.arg_parser.add_subparsers(dest=self.subcommand_label(), required=True)
            self.add_upgrade_parser(subparsers)

        def add_upgrade_parser(self, subparsers):
            self.__upgrade_parser = subparsers.add_parser("upgrade")
            self.__upgrade_parser.add_argument("package")
            self.__upgrade_parser.add_argument("version", nargs='?')
            self.__upgrade_parser.add_argument("-l", "--last", action="store_true")
            self.__upgrade_parser.add_argument("-c", "--commit", action="store_true")
            self.__upgrade_parser.add_argument("-p", "--push", action="store_true")

        def upgrade(self, args):
            cmake_project = CMakeProject(".")
            if args.last:
                if args.version:
                    self.__upgrade_parser.print_help()
                    print(f"\nerror: -l, --last option is provided, so version ({args.version}) argument is not needed.")
                    exit(-1)
                else:
                    raise "error: cmakepj dependency upgrade -l <package>  is not implemented yet!"
            elif args.version is None:
                self.__upgrade_parser.print_help()
                print(f"\nerror: version argument is required when -l option is not provided.")
                exit(-1)
            else:
                cmake_project.upgrade_dependency_version(args.package, args.version, args.commit)


if __name__ == "__main__":
    # https://iridakos.com/programming/2018/03/01/bash-programmable-completion-tutorial
    # cmpj -v --version
    # cmpj create exe|lib|hlib|hw [name]
    # cmpj version set <version> [--commit] [--push]
    #. cmpj version upgrade major|minor|patch [--commit] [--push]
    #. cmpj submodule set-branch <module> <branch> [--last] [--commit] [--push]
    #. cmpj dependency upgrade <package> <version> [--last] [--commit] [--push]
    #. cmpj release start|finish|create

    # cmpj version upgrade -cp minor
    # cmpj submodule set-branch cmtk --last
    # cmpj release start|finish|create

    # cmpj version upgrade -cp minor
    # cmpj dependency upgrade arba-core --last
    # cmpj release start|finish|create

    cmpj = Cmakepj()
    cmpj.invoke(cmpj.arg_parser.parse_args())

    print('EXIT SUCCESS')
