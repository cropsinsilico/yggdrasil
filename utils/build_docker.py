# TODO: Remove platform from tag?
import os
import platform
import sys
import argparse
import subprocess
import json
import shutil
import urllib.request
_utils_dir = os.path.dirname(__file__)
_tmp_dir = os.path.join(_utils_dir, '_tmp_dockerfiles')
_ygg_github_api = "https://api.github.com/repos/cropsinsilico/yggdrasil"


def image_exists(tag):
    r"""Determine if a docker image exists.

    Args:
        tag (str): Tag to check for.

    Returns:
        bool: True if the image exists, False otherwise.

    """
    # TODO: Actually check
    args = ['docker', 'image', 'inspect', tag, '--format="ignore me"']
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        return False
    return True


class FileCopy(object):
    r"""Class for managing a file copied into an image.

    Args:
        source (str): Path to local file that should be copied. Can be
            an absolute or relative path (taken relative to the working
            directory).
        source_dir (str, optional): Root directory within the source
            that corresponds with the docker_dir.
        context (str, optional): Path to the context that docker
            build will be called with.
        docker_dir (str, optional): Directory within the docker
            image that the source should be copied into, replicating the
            path to the file starting at source_dir.
        local_dir (str, optional): Name of intermediate directory within
            the docker context that should be used for copying files from
            outside the docker context.

    """

    _parent_context_dir = 'parent_context'

    def __init__(self, source, source_dir=None, context=_utils_dir,
                 docker_dir='/yggdrasil', local_dir='parent_context',
                 stage=None):
        if source_dir is None:
            source_dir = os.path.dirname(_utils_dir)
        self.source = source
        self.source_dir = source_dir
        self.context = context
        self.docker_dir = docker_dir
        for k in ['source', 'source_dir', 'context']:
            v = getattr(self, k)
            # if not os.path.isabs(v):
            setattr(self, k, os.path.normpath(v))
        self.local_dir = os.path.join(self.context, local_dir)
        self.stage = stage
        self.inside_context = self.source_dir.startswith(self.context)
        self.base = os.path.relpath(self.source, self.source_dir)
        if self.inside_context:
            self.source_context = self.source
        else:
            self.source_context = os.path.join(self.local_dir, self.base)
        self.source_local = os.path.relpath(
            self.source_context, self.context)
        self.docker_path = os.path.join(self.docker_dir, self.base)

    @property
    def docker_copy_command(self):
        r"""str: Docker command to copy file from the context into the
        image."""
        return f'COPY {self.source_local} {self.docker_path}'

    def ensure_local(self):
        r"""Ensure that there is a local copy of the file within the
        context that can be copied via the docker COPY command.

        Returns:
            list: Set of files or directories created.

        """
        if self.inside_context:
            return []
        out = []
        parent = os.path.dirname(self.source_context)
        if not os.path.isdir(parent):
            os.makedirs(parent)
            out.append(parent)
        shutil.copy2(self.source, self.source_context)
        out.append(self.source_context)
        return out


# Builder classes
class BuilderMeta(type):
    r"""Meta class for builders."""

    _registry = {}

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if cls._name is not None:
            meta._registry[cls._name] = cls
        return cls


class BuilderBase(object, metaclass=BuilderMeta):
    r"""Class for building docker image.

    Args:
        args (argparse.Namespace): Parsed arguments.
        context (str, optional): Directory that should be provided as the
            context for the image. Defaults to the directory containing
            this script.
        base (BuilderBase, optional): Base builder for the image that
            this image depends on.
        **kwargs: Additional keyword arguments are passed to the base
            class constructure if base is not provided and this builder
            requires a base.

    """

    _name = None
    _dockerfile = None
    _repo = None
    _copy_flags = {}
    _allows_push = True

    def __init__(self, args, context=_utils_dir,
                 tag=None, **kwargs):
        self._generated = []
        self.args = args
        self.context = context
        self._tag = tag
        self.platform = args.platform
        self.copy_files = {}
        for k in self._copy_flags.keys():
            v = getattr(args, f'copy_{k}')
            if v:
                self.add_copy_files(v, stage=k)
                # Prevent other classes from using this
                setattr(args, f'copy_{k}', None)
        if not self.platform:
            if ((sys.platform == 'darwin'
                 and platform.machine().lower() == 'arm64')):
                self.platform = 'arm64'
            else:
                self.platform = 'amd64'

    def add_copy_files(self, files, stage=None):
        r"""Add a set of files to the class.

        Args:
            files (list): Set of files to add.
            stage (str, optional): Stage that files should be copied at
                in the docker image.

        """
        files = [
            FileCopy(x, context=self.context, stage=stage) for x in files
        ]
        for x in files:
            if x.stage not in self._copy_flags:
                self.error(f'File copying not supported for stage: '
                           f'{x.stage}')
            self.copy_files.setdefault(x.stage, [])
            self.copy_files[x.stage].append(x)

    @classmethod
    def create_builder(cls, args, name=None, **kwargs):
        r"""Create a builder instance.

        Args:
        args (argparse.Namespace): Parsed arguments.
            name (str, optional): Name of the builder class to use. If
                not provided, this class will be used.
            **kwargs: Additional keyword arguments are passed to the
                class constructor.

        Returns:
            BuilderBase: Builder instance.
        
        """
        if name is None:
            name = cls.args2class(args)
        cls = BuilderMeta._registry[name]
        out = cls(args, **kwargs)
        return out

    @classmethod
    def args2class(cls, args, for_base=False):
        r"""Get a builder class based on the arguments.

        Args:
            args (argparse.Namespace): Parsed arguments.
            for_base (bool, optional): If True, determine the base class
                excluding explicit type information.

        Returns:
            str: Name of the builder class that should be used.

        """
        if (not for_base) and args.type and args.type != 'environment':
            name = args.type
        elif args.local:
            name = 'local'
        elif args.commit or args.branch:
            if args.branch and not args.commit:
                args.commit = 'latest'
            name = 'commit'
        elif args.conda_version:
            name = 'conda-release'
        else:
            name = 'release'
        return name

    def error(self, cls, message=''):
        r"""Raise an error message with some context.

        Args:
            cls (type): Error class to raise.
            message (str, optional): Error message.

        """
        raise cls(f'{self._name}: {message}')

    def log(self, message=''):
        r"""Emit a log message.

        Args:
            message (str, optional): Log message.

        """
        print(f'{self._name}: {message}')

    def call(self, args, context='', dry_run=None, **kwargs):
        r"""Call a subprocess.

        Args:
            args (list): Argument list.
            context (str, optional): Context for log message.
            dry_run (bool, optional): If True, show the command, but dont
                run it.
            **kwargs: Additional keyword arguments are passed to
                subprocess.call.

        """
        self.log(f"{context}\"{' '.join(args)}\"")
        if dry_run is None:
            dry_run = self.args.dry_run
        if dry_run:
            return
        subprocess.call(args, **kwargs)

    def cleanup(self, **kwargs):
        r"""Clean up files produced by a build."""
        # for k in self._generated:
        #     if os.path.isfile(k):
        #         os.remove(k)
        #     elif os.path.isdir(k):
        #         os.rmdir(k)
        pass

    @property
    def repo(self):
        r"""str: DockerHub repository that the image should be pushed
        to."""
        if self._repo is not None:
            return self._repo
        return f'cropsinsilico/yggdrasil-{self._name}'

    @property
    def dockerfile(self):
        r"""str: Path to the docker file to build."""
        base = self._dockerfile
        if base is None:
            base = f'{self._name.replace("-", "_")}.Docker'
        out = os.path.join(_utils_dir, base)
        return out

    def generate_tag(self, base):
        r"""Generate a tag including platform information.

        Args:
            base (str): Tag base.

        Returns:
            str: Tag.

        """
        out = base
        if self.platform != 'amd64':
            out += f'-{self.platform}'
        return out

    @property
    def tag(self):
        r"""str: Image tag."""
        return self.generate_tag(self._tag)

    @property
    def tag_latest(self):
        r"""str: String for latest tag."""
        return self.generate_tag('latest')

    @property
    def dockertag(self):
        r"""str: Image tag with repo."""
        if not self.repo:
            return self.tag
        return f'{self.repo}:{self.tag}'

    @property
    def dockertag_latest(self):
        r"""str: Latest image tag with repo."""
        if not self.repo:
            return self.tag_latest
        return f'{self.repo}:{self.tag_latest}'

    @property
    def exists(self):
        r"""bool: True if the image exists."""
        return image_exists(self.dockertag)

    @property
    def args_build(self):
        r"""list: Arguments for docker build."""
        out = ['--build-arg', f'python={self.args.python}']
        return out

    def build(self, top_level=True, verbose=None, dry_run=None):
        r"""Build the image and any non-existent base images.

        Args:
            top_level (bool, optional): True if this is the top-level
                build call (i.e. not built as a dependency).
            verbose (bool, optional): If True, turn on verbose output
                for the build.
            dry_run (bool, optional): If True, show the build commands,
                but dont run them.

        """
        if verbose is None:
            verbose = self.args.verbose
        if dry_run is None:
            dry_run = self.args.dry_run
        dockerfile = self.dockerfile
        self.log(f'Building \"{dockerfile}\"')
        try:
            if self.copy_files:
                old = dockerfile
                dockerfile = old + '_copy'
                # if not os.path.isdir(_tmp_dir):
                #     os.mkdir(_tmp_dir)
                # dockerfile = os.path.join(
                #     _tmp_dir, os.path.basename(old) + '_copy')
                contents = open(old, 'r').read()
                for stage, files in self.copy_files.items():
                    copy_flag = self._copy_flags[stage]
                    for x in files:
                        self._generated += x.ensure_local()
                    assert contents.count(copy_flag) == 1
                    new_contents = [x.docker_copy_command for x in files]
                    new_contents = (
                        copy_flag + '\n' + '\n'.join(new_contents)
                    )
                    contents = new_contents.join(
                        contents.split(copy_flag))
                with open(dockerfile, 'w') as fd:
                    fd.write(contents)
            args = [
                'docker', 'build', '-t', self.dockertag,
                '-f', dockerfile,
                '--platform', f'linux/{self.platform}'
            ]
            if self.args.sudo:
                args.insert(0, 'sudo')
            args += self.args_build
            if verbose:
                args += ['--progress', 'plain']
            args.append(self.context)
            if not self.args.dont_build:
                self.call(args, 'BUILD: ')
                if (not dry_run) and (not self.exists):
                    self.error(
                        RuntimeError,
                        f"Failed to build image \"{self.dockertag}\""
                    )
            if not (self.args.disable_latest or self.args.dont_build):
                assert self.repo
                args = [
                    'docker', 'tag', self.dockertag,
                    self.dockertag_latest,
                ]
                self.call(args, 'TAG LATEST: ', cwd=None)  # TODO:?
        finally:
            if top_level:
                self.cleanup()

    @property
    def args_run(self):
        r"""list: docker run arguments for this image."""
        return ['-dit']

    def run(self):
        r"""Run the docker image."""
        args = ['docker', 'run'] + self.args_run + [self.dockertag]
        self.call(args, 'RUN: ')

    @property
    def args_push(self):
        r"""list: docker push arguments for this image."""
        return []

    def push(self, tag=None):
        r"""Push the docker image to DockerHub.

        Args:
            tag (str): Tag (with repo name) to push other than the
                default.

        """
        if not self._allows_push:
            self.error(RuntimeError, 'Push not allowed')
        do_latest = (tag is None and not self.args.disable_latest)
        if tag is None:
            tag = self.dockertag
        args = ['docker', 'push'] + self.args_push + [tag]
        self.call(args, 'PUSH: ')
        if do_latest:
            self.push(tag=self.dockertag_latest)


# Builders that install yggdrasil
class InstallBuilderBase(BuilderBase):
    r"""Base class for builders that install yggdrasil."""

    _is_root = True


class ReleaseBuilder(InstallBuilderBase):
    r"""Class for building an environment from a specific version of
    yggdrasil.

    Args:
        args (argparse.Namespace): Parsed arguments.
        version (str, optional): Version that should be installed. If not
            provided, the latest release will be used.

    """

    _name = 'release'
    _dockerfile = 'commit.Docker'
    _repo = 'cropsinsilico/yggdrasil'

    def __init__(self, args, version=None, **kwargs):
        if version is None:
            version = args.version
        if version is None:
            url = f"{_ygg_github_api}/tags"
            tags = json.loads(urllib.request.urlopen(url).read())
            version = max(tags, key=lambda x: x['name'])['name'].lstrip('v')
        self.version = version
        tag = f'v{version}'
        super(ReleaseBuilder, self).__init__(args, tag=tag, **kwargs)

    @property
    def args_build(self):
        r"""list: Arguments for docker build."""
        out = ['--build-arg', f'commit=tags/v{self.version}']
        out += super(ReleaseBuilder, self).args_build
        return out


class CondaReleaseBuilder(ReleaseBuilder):
    r"""Class for building an environment from a specific version of
    yggdrasil installed via conda.

    Args:
        args (argparse.Namespace): Parsed arguments.
        version (str, optional): Version that should be installed. If not
            provided, the latest release will be used.

    """

    _name = 'conda-release'
    _dockerfile = 'release.Docker'
    _copy_flags = {
        'install': '# Copy installation files',
        'config': '# Copy configuration files',
        'local': '# Copy local files',
    }

    def __init__(self, args, version=None, **kwargs):
        if version is None:
            version = args.conda_version
        super(CondaReleaseBuilder, self).__init__(args, version=version,
                                                  **kwargs)
            
    @property
    def args_build(self):
        r"""list: Arguments for docker build."""
        out = ['--build-arg', f'version={self.version}']
        # Skip above parent class
        out += super(ReleaseBuilder, self).args_build
        return out


class CommitBuilder(InstallBuilderBase):
    r"""Class for building an environment from a specific commit.

    Args:
        args (argparse.Namespace): Parsed arguments.
        commit (str): Yggdrasil commit that should be built.
        branch (str, optional): Branch that should be used if commit is
            'latest'.

    """

    _name = 'commit'
    _repo = 'cropsinsilico/yggdrasil-dev'
    _copy_flags = {
        'setup': '# Copy setup files',
        'install': '# Copy installation files',
        'config': '# Copy configuration files',
        'local': '# Copy local files',
    }

    def __init__(self, args, commit=None, branch=None, **kwargs):
        if commit is None:
            commit = args.commit
        if branch is None:
            branch = args.branch
        if commit == 'latest':
            if branch is None:
                branch = 'main'
            url = f"{_ygg_github_api}/commits/{branch}"
            response = json.loads(urllib.request.urlopen(url).read())
            commit = response['sha']
        self.commit = commit
        self.branch = branch
        super(CommitBuilder, self).__init__(args, tag=self.commit,
                                            **kwargs)

    @property
    def args_build(self):
        r"""list: Arguments for docker build."""
        out = ['--build-arg', f'commit={self.commit}']
        out += super(CommitBuilder, self).args_build
        return out


class LocalBuilder(InstallBuilderBase):
    r"""Class for building a docker image from the local yggdrasil
    source code.

    Args:
        args (argparse.Namespace): Parsed arguments.
        source_dir (str): Path to the directory containing yggdrasil.
        commit (str, optional): Commit that should be built.

    """

    _name = 'local'
    _allows_push = False

    def __init__(self, args, source_dir=None, commit=None, **kwargs):
        if source_dir is None:
            source_dir = args.local
        if commit is None:
            commit = args.commit
        if source_dir is None:
            source_dir = os.path.dirname(_utils_dir)
        source_dir = os.path.abspath(source_dir)
        if commit is None:
            commit = 'latest'
        if commit == 'latest':
            import git
            repo = git.Repo(source_dir)
            commit = str(repo.commit())
            if repo.is_dirty():
                commit += '-dirty'
            repo.close()
        self.source_dir = source_dir
        self.commit = commit
        super(LocalBuilder, self).__init__(args, tag=self.commit,
                                           **kwargs)

    @property
    def args_build(self):
        r"""list: Arguments for docker build."""
        source_dir = os.path.relpath(self.source_dir, self.context) + '/'
        out = ['--build-arg', f'sourcedir={source_dir}']
        out += super(LocalBuilder, self).args_build
        return out


# Classes for images based on installations
class ExtensionBuilderBase(BuilderBase):
    r"""Class for building docker images based on other images.

    Args:
        args (argparse.Namespace): Parsed arguments.
        base (BuilderBase, optional): Base builder for the image that
            this image depends on.
        **kwargs: Additional keyword arguments are passed to the base
            class constructure if base is not provided and the BuilderBase
            constructor.

    """

    _is_root = False
    _base_class = None

    def __init__(self, args, base=None, **kwargs):
        self.base = base
        if self.base is None:
            base_class = self._base_class
            if not isinstance(base_class, str):
                base_class = self.args2class(args, for_base=True)
            self.base = self.create_builder(args, name=base_class,
                                            **kwargs)
        super(ExtensionBuilderBase, self).__init__(args, **kwargs)

    @property
    def repo(self):
        r"""str: DockerHub repository that the image should be pushed
        to."""
        if self._repo is None:
            return self.base.repo.replace(
                'yggdrasil', f'yggdrasil-{self._name}')
        return super(ExtensionBuilderBase, self).repo

    @property
    def tag(self):
        r"""str: Image tag."""
        return self.base.tag

    @property
    def tag_latest(self):
        r"""str: String for latest tag."""
        return self.base.tag_latest

    @property
    def args_build(self):
        r"""list: Arguments for docker build."""
        out = super(ExtensionBuilderBase, self).args_build
        out += ['--build-arg', f'base={self.base.dockertag}']
        return out

    def build(self, top_level=True, **kwargs):
        r"""Build the image and any non-existent base images.

        Args:
            top_level (bool, optional): True if this is the top-level
                build call (i.e. not built as a dependency).
            **kwargs: Additional keyword arguments are passed to the
                base class's build method and the parent class's method.

        """
        if not self.base.exists:
            self.base.build(top_level=False, **kwargs)
        super(ExtensionBuilderBase, self).build(
            top_level=top_level, **kwargs)

    def cleanup(self, **kwargs):
        r"""Clean up files produced by a build."""
        super(ExtensionBuilderBase, self).cleanup(**kwargs)
        self.base.cleanup(**kwargs)


class ExecutableBuilder(ExtensionBuilderBase):
    r"""Class for building a docker image from the local yggdrasil
    source code."""

    _name = 'executable'


class ServiceBuilder(ExtensionBuilderBase):
    r"""Class for building a docker image that runs a yggdrasil
    integration service manager."""

    _name = 'service'

    @property
    def args_run(self):
        r"""list: docker run arguments for this image."""
        out = super(ServiceBuilder, self).args_run
        out += ['-p', '5000:5000', '-e', 'PORT=5000']
        return out


class LoadedServiceBuilder(ServiceBuilder):
    r"""Class for building a docker image that runs a yggdrasil
    integration service manager with models loaded.

    Args:
        args (argparse.Namespace): Parsed arguments.
        model_repo_commit (str, optional): Commit from the yggdrasil
            model repository that models should be loaded from.
        **kwargs: Additional keyword arguments are passed to the parent
            class constructor.

    """

    _name = 'loaded-service'
    _base_class = 'service'

    def __init__(self, args, model_repo_commit=None, **kwargs):
        if model_repo_commit is None:
            model_repo_commit = args.model_repo_commit
        if model_repo_commit is None:
            model_repo_commit = 'latest'
        if model_repo_commit == 'latest':
            url = ("https://api.github.com/repos/cropsinsilico/"
                   "yggdrasil_models/commits/main")
            response = json.loads(urllib.request.urlopen(url).read())
            model_repo_commit = response['sha']
        self.model_repo_commit = model_repo_commit
        super(LoadedServiceBuilder, self).__init__(args, **kwargs)

    @property
    def tag(self):
        r"""str: Image tag."""
        out = super(LoadedServiceBuilder, self).tag
        out += f'-{self.model_repo_commit}'
        return out

    @property
    def args_build(self):
        r"""list: Arguments for docker build."""
        out = super(LoadedServiceBuilder, self).args_build
        out += ['--build-arg', f'commit={self.model_repo_commit}']
        return out


class ExternalBuilder(ExtensionBuilderBase):
    r"""Class for building an external docker images that uses yggdrasil
    as its base.

    Args:
        args (argparse.Namespace): Parsed arguments.
        **kwargs: Additional keyword arguments are passed to the parent
            class constructor.

    """

    _name = 'external'

    def __init__(self, args, dockerfile=None, repo=None,
                 context=None, **kwargs):
        if dockerfile is None:
            dockerfile = args.dockerfile
        if repo is None:
            repo = args.repo
        if context is None:
            context = os.path.dirname(dockerfile)
        self.external_dockerfile = dockerfile
        self.external_repo = repo
        super(ExternalBuilder, self).__init__(args, context=context,
                                              **kwargs)

    @property
    def dockerfile(self):
        r"""str: Path to the docker file to build."""
        return self.external_dockerfile

    @property
    def repo(self):
        r"""str: DockerHub repository that the image should be pushed
        to."""
        return self.external_repo


def add_argument_subparsers(subparsers, *args, group=False, **kwargs):
    r"""Add an argument to all of the subparsers in a set.

    Args:
        subparsers (list): Subparsers to add argument to.
        group (bool, optional): If True, one mutually exclusive group
            will be initialized for each subparser and the list will be
            returned.
        *args, **kwargs: Additional arguments are passed to add_argument
            for each subparser.

    """
    if not isinstance(subparsers, list):
        subparsers = [subparsers]
    out = []
    for i, x in enumerate(subparsers):
        if group:
            out.append(x.add_mutually_exclusive_group())
        else:
            x.add_argument(*args, **kwargs)
    if group:
        return out


class GroupWrapper(object):
    
    def __init__(self, groups=None):
        if groups is None:
            groups = []
        self.groups = groups

    def append(self, group):
        self.groups.append(group)

    def add_argument(self, *args, **kwargs):
        for x in self.groups:
            x.add_argument(*args, **kwargs)

    def add_mutually_exclusive_group(self, *args, **kwargs):
        return GroupWrapper([
            x.add_mutually_exclusive_group(*args, **kwargs)
            for x in self.groups
        ])

                
class ArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        self._subparsers_sets = {}
        self._subparsers_objects = {}
        super(ArgumentParser, self).__init__(*args, **kwargs)

    def add_subparsers(self, *args, **kwargs):
        name = kwargs['dest']
        assert name not in self._subparsers_objects
        out = super(ArgumentParser, self).add_subparsers(*args, **kwargs)
        self._subparsers_objects[name] = out
        self._subparsers_sets[name] = GroupWrapper()
        return out

    def add_subparser(self, name, *args, **kwargs):
        assert name in self._subparsers_objects
        out = self._subparsers_objects[name].add_parser(*args, **kwargs)
        self._subparsers_sets[name].append(out)
        return out

    def add_argument(self, *args, **kwargs):
        if self._subparsers_objects:
            for v in self._subparsers_sets.values():
                v.add_argument(*args, **kwargs)
            return
        super(ArgumentParser, self).add_argument(*args, **kwargs)

    def add_mutually_exclusive_group(self, *args, **kwargs):
        if self._subparsers_objects:
            return GroupWrapper([
                v.add_mutually_exclusive_group(*args, **kwargs)
                for v in self._subparsers_sets.values()
            ])
        return super(ArgumentParser, self).add_mutually_exclusive_group(
            *args, **kwargs)


if __name__ == "__main__":
    parser = ArgumentParser(
        "Build a docker image containing a version of yggdrasil.")

    # Subparsers
    subparsers = parser.add_subparsers(
        dest="type",
        help=("Type of docker image that should be built "
              "(Defaults to 'environment')."))
    parser_env = parser.add_subparser(
        "type", "environment",
        help="Image that will be used as a virutal environment.")
    parser_exe = parser.add_subparser(
        "type", "executable",
        help="Executable image for running yggdrasil integrations.")
    parser_srv = parser.add_subparser(
        "type", "service",
        help=("Service image for running a yggdrasil integrations service "
              "manager web application."))

    # Mutually exclusive group
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--version", type=str,
        help="Yggdrasil release that should be installed in the image.")
    group.add_argument(
        "--commit", type=str,
        help="Yggdrasil commit that should be installed in the image.")
    group.add_argument(
        "--branch", type=str,
        help="Yggdrasil branch that should be installed in the image.")
    group.add_argument(
        "--conda-version", type=str,
        help="Yggdrasil conda release that should be installed in the image.")
    group.add_argument(
        "--local", type=str,
        help=("Local directory containing yggdrasil version that should "
              "be installed in the image."))

    # General arguments
    parser.add_argument(
        "--python", type=str, default="3.11",
        help="Version of Python that should be used")
    parser.add_argument(
        "--platform", type=str,
        help="Platform that should be used for base image")
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show build output")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print build commant, but don't actually run it")
    parser.add_argument(
        "--push", action="store_true",
        help="After successfully building the image, push it to DockerHub.")
    parser.add_argument(
        "--run", action="store_true",
        help="After successfully building the image, run it.")
    parser.add_argument(
        "--dont-build", action="store_true",
        help="Don't build the image.")
    parser.add_argument(
        "--disable-latest", action="store_true",
        help=("Don't tag the new image as 'latest' in addition to the "
              "version/commit specific tag."))
    parser.add_argument(
        "--copy-setup", nargs='+', type=str, action='extend',
        help=("Copy one or more files from the parent context into the "
              "build context, adding \"COPY\" commands to the docker "
              "file before the yggdrasil environment is set up."))
    parser.add_argument(
        "--copy-install", nargs='+', type=str, action='extend',
        help=("Copy one or more files from the parent context into the "
              "build context, adding \"COPY\" commands to the docker "
              "file after the yggdrasil environment is set up, but "
              "before yggdrasil is installed."))
    parser.add_argument(
        "--copy-config", nargs='+', type=str, action='extend',
        help=("Copy one or more files from the parent context into the "
              "build context, adding \"COPY\" commands to the docker "
              "file after yggdrasil has been installed, but before it "
              "is configured."))
    parser.add_argument(
        "--copy-local", "--copy", nargs='+', type=str, action='extend',
        help=("Copy one or more files from the parent context into the "
              "build context, adding \"COPY\" commands to the docker "
              "file after yggdrasil has been installed and configured."))
    parser.add_argument(
        "--sudo", action='store_true',
        help=("Run build with sudo"))
    # Subparser specific arguments
    parser_srv.add_argument(
        "--model-repo-commit", type=str,
        help=("Commit from the yggdrasil model repository that should "
              "be cloned inside the image and used to populate the "
              "service. If not provided, no models will be pre-loaded"))
    parser_ext = subparsers.add_parser(
        "external",
        help=("Build a Docker image from an external Dockerfile that "
              "uses one of the yggdrasil images"))
    parser_ext.add_argument(
        "--dockerfile", type=str,
        default=os.path.join(os.getcwd(), 'Dockerfile'),
        help="Docker file that an image should be built for")
    parser_ext.add_argument(
        "--repo", type=str,
        help="Repository that the built image should be pushed to")
    args = parser.parse_args()
    builder = BuilderBase.create_builder(args)
    builder.build()
    if args.run:
        builder.run()
    if args.push:
        builder.push()
