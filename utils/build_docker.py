# TODO: Remove platform arg and just use the CLI option
import os
import platform
import sys
import argparse
import subprocess
import json
import urllib.request
_utils_dir = os.path.dirname(__file__)


def image_exists(tag):
    r"""Determine if a docker image exists.

    Args:
        tag (str): Tag to check for.

    Returns:
        bool: True if the image exists, False otherwise.

    """
    # TODO: Actually check
    return False


def build(parsed_args, dockerfile=None, tag=None, flags=None,
          repo='cropsinsilico/yggdrasil', context=_utils_dir, cwd=None,
          base_params=None, top_level=False):
    r"""Build a docker image.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments.
        dockerfile (str): Full path to the docker file that should be used.
        tag (str): Tag that should be added to the image.
        flags (list, optional): Additional flags that should be passed to
            the build command. Defaults to [].
        repo (str, optional): DockerHub repository that the image will be
            pushed to. Defaults to 'cropsinsilico/yggdrasil'.
        context (str, optional): Directory that should be provided as the
            context for the image. Defaults to the directory containing this
            script.
        base_params (dict, optional): Parameters for the base image.

    """
    # TODO: Update so multiple targets are built
    # https://docs.docker.com/build/building/multi-platform/
    # TODO: Update sysv_ipc & czmq to have linux/aarch64 builds
    if flags is None:
        flags = []
    if not parsed_args.platform:
        if sys.platform == 'darwin' and platform.machine().lower() == 'arm64':
            parsed_args.platform = 'arm64'
        else:
            parsed_args.platform = 'amd64'
    if sys.platform == 'darwin' and platform.machine().lower() == 'arm64':
        assert parsed_args.platform == 'arm64'
    if parsed_args.platform != 'amd64':
        tag += f'-{parsed_args.platform}'
    if parsed_args.verbose:
        flags += ['--progress', 'plain']
    if repo:
        assert tag
        docker_tag = f'{repo}:{tag}'
    else:
        assert tag
        docker_tag = tag
    if base_params:
        base_tag = f"{base_params['repo']}:{base_params['tag']}"
        if parsed_args.platform != 'amd64':
            base_tag += f'-{parsed_args.platform}'
        flags += ['--build-arg', f'base={base_tag}']
        if not image_exists(base_tag):
            build(parsed_args, **base_params)
    flags += ['--build-arg', f'python={parsed_args.python}',
              '--build-arg', f'platform={parsed_args.platform}']
    args = ['docker', 'build', '-t', docker_tag, '-f', dockerfile,
            '--platform', f'linux/{parsed_args.platform}'] + flags
    args.append(context)
    if parsed_args.dry_run:
        print(f"BUILD: \"{' '.join(args)}\"")
    else:
        subprocess.call(args)
    if not parsed_args.disable_latest:
        assert repo
        latest_tag = 'latest'
        if parsed_args.platform != 'amd64':
            latest_tag += f'-{parsed_args.platform}'
        args = ['docker', 'tag', docker_tag, f"{repo}:{latest_tag}"]
        if parsed_args.dry_run:
            print(f"TAG LATEST: \"{' '.join(args)}\"")
        else:
            subprocess.call(args, cwd=cwd)
    if parsed_args.run and top_level:
        run_image(parsed_args, tag, repo=repo)
    if parsed_args.push:
        assert not repo.endswith('-local')
        push_image(parsed_args, tag, repo=repo)
        if not parsed_args.disable_latest:
            push_image(parsed_args, 'latest', repo=repo)


def push_image(parsed_args, tag, repo='cropsinsilico/yggdrasil'):
    r"""Push a docker image to DockerHub.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments.
        tag (str): Tag that should be added to the image.
        repo (str, optional): DockerHub repository that the image will be
            pushed to. Defaults to 'cropsinsilico/yggdrasil'.

    """
    assert repo and tag
    args = ['docker', 'push', f'{repo}:{tag}']
    if parsed_args.dry_run:
        print(f"PUSH: \"{' '.join(args)}\"")
    else:
        subprocess.call(args)


def run_image(parsed_args, tag, repo='cropsinsilico/yggdrasil'):
    r"""Run a docker image.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments.
        tag (str): Tag that should be added to the image.
        repo (str, optional): DockerHub repository for the image that
            will be run. Defaults to 'cropsinsilico/yggdrasil'.

    """
    assert repo and tag
    args = ['docker', 'run', '-dit']
    if parsed_args.type == 'service':
        args += ['-p', '5000:5000', '-e', 'PORT=5000']
    args += [f'{repo}:{tag}']
    if parsed_args.dry_run:
        print(f"RUN: \"{' '.join(args)}\"")
    else:
        subprocess.call(args)


def params_release(version):
    r"""Get parameters to build a docker image containing an yggdrasil
    release.

    Args:
        version (str): Release version to install in the image.

    Returns:
        dict: Docker build parameters.

    """
    if version is None:
        url = "https://api.github.com/repos/cropsinsilico/yggdrasil/tags"
        tags = json.loads(urllib.request.urlopen(url).read())
        version = max(tags, key=lambda x: x['name'])['name'].lstrip('v')
    dockerfile = os.path.join(_utils_dir, 'commit.Docker')
    tag = f'v{version}'
    flags = ['--build-arg', f'commit=tags/v{version}']
    repo = 'cropsinsilico/yggdrasil'
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


def params_conda_release(version):
    r"""Get parameters to build a docker image containing an yggdrasil
    release installed from conda.

    Args:
        version (str): Release version to install in the image.

    Returns:
        dict: Docker build parameters.

    """
    if version is None:
        url = "https://api.github.com/repos/cropsinsilico/yggdrasil/tags"
        tags = json.loads(urllib.request.urlopen(url).read())
        version = max(tags, key=lambda x: x['name'])['name'].lstrip('v')
    dockerfile = os.path.join(_utils_dir, 'release.Docker')
    tag = f'v{version}'
    flags = ['--build-arg', f'version={version}']
    repo = 'cropsinsilico/yggdrasil'
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


def params_commit(commit, branch=None):
    r"""Get parameters to build a docker image containing a version of
    yggdrasil specific to a commit.

    Args:
        commit (str): ID for commit to install from the yggdrasil git
            repo. If 'latest', the most recent commit on the specified
            branch will be used.
        branch (str, optional): Branch that commit should come from if
            commit is 'latest'. Defaults to 'main' if not provided.

    Returns:
        dict: Docker build parameters.

    """
    dockerfile = os.path.join(_utils_dir, 'commit.Docker')
    if commit == 'latest':
        if branch is None:
            branch = 'main'
        url = ("https://api.github.com/repos/cropsinsilico/yggdrasil/"
               "commits/" + branch)
        response = json.loads(urllib.request.urlopen(url).read())
        commit = response['sha']
    tag = commit
    flags = ['--build-arg', f'commit={commit}']
    repo = 'cropsinsilico/yggdrasil-dev'
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


def params_local(source_dir, commit=None):
    r"""Get parameters to build a docker image containing a local version
    yggdrasil.

    Args:
        source_dir (str): Path to the directory containing yggdrasil.

    Returns:
        dict: Docker build parameters.

    """
    source_dir = os.path.abspath(source_dir)
    dockerfile = os.path.join(_utils_dir, 'local.Docker')
    if commit is None:
        commit = 'latest'
    if commit == 'latest':
        import git
        repo = git.Repo(source_dir)
        commit = str(repo.commit())
        if repo.is_dirty():
            commit += '-dirty'
        repo.close()
    tag = commit
    context = _utils_dir
    source_dir = os.path.relpath(source_dir, context) + '/'
    flags = ['--build-arg', f'sourcedir={source_dir}']
    repo = 'cropsinsilico/yggdrasil-local'
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo,
                context=context)


def params_executable(params):
    r"""Get parameters to build a docker image containing a version of
    yggdrasil specific to a commit or tagged release that can be used as an
    executable.

    Args:
        params (dict): Docker build parameters set based on the base type.

    Returns:
        dict: Docker build parameters.

    """
    dockerfile = os.path.join(_utils_dir, 'executable.Docker')
    repo = params["repo"]
    tag = params["tag"]
    repo = repo.replace('yggdrasil', 'yggdrasil-executable')
    return dict(dockerfile=dockerfile, tag=tag, repo=repo,
                base_params=params)


def params_service(params, model_repo_commit=False):
    r"""Get parameters to build a docker image containing a version of
    yggdrasil sepcific to a commit or tagged release that runs an yggdrasil
    integration service manager.

    Args:
        params (dict): Docker build parameters set based on the base type.
        model_repo_commit (str, optional): Commit from yggdrasil model
            repository that should be cloned inside the image.

    Returns:
        dict: Docker build parameters.

    """
    repo = params["repo"]
    tag = params["tag"]
    if model_repo_commit:
        base_params = params_service(params)
        repo = repo.replace('yggdrasil', 'yggdrasil-loaded-service')
        dockerfile = os.path.join(_utils_dir, 'loaded_service.Docker')
        if model_repo_commit == 'latest':
            url = ("https://api.github.com/repos/cropsinsilico/"
                   "yggdrasil_models/commits/main")
            response = json.loads(urllib.request.urlopen(url).read())
            model_repo_commit = response['sha']
    else:
        base_params = params
        repo = repo.replace('yggdrasil', 'yggdrasil-service')
        dockerfile = os.path.join(_utils_dir, 'service.Docker')
    flags = []
    if model_repo_commit:
        tag += f'-{model_repo_commit}'
        flags += ['--build-arg', f'commit={model_repo_commit}']
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo,
                base_params=base_params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Build a docker image containing a version of yggdrasil.")
    # parser.add_argument(
    #     "type", type=str, default="environment",
    #     choices=["environment", "executable", "service"],
    #     help=("Type of docker image that should be built."
    #           ""))
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
        "--disable-latest", action="store_true",
        help=("Don't tag the new image as 'latest' in addition to the "
              "version/commit specific tag."))
    subparsers = parser.add_subparsers(
        dest="type",
        help=("Type of docker image that should be built "
              "(Defaults to 'environment')."))
    parser_env = subparsers.add_parser(
        "environment",
        help="Image that will be used as a virutal environment.")
    parser_exe = subparsers.add_parser(
        "executable",
        help="Executable image for running yggdrasil integrations.")
    parser_srv = subparsers.add_parser(
        "service",
        help=("Service image for running a yggdrasil integrations service "
              "manager web application."))
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
    if args.local:
        params = params_local(args.local, commit=args.commit)
    elif args.commit or args.branch:
        if args.branch and not args.commit:
            args.commit = 'latest'
        params = params_commit(args.commit, branch=args.branch)
    elif args.conda_version:
        params = params_conda_release(args.conda_version)
    else:
        params = params_release(args.version)
    if args.type == 'executable':
        params = params_executable(params)
    elif args.type == 'service':
        params = params_service(params,
                                model_repo_commit=args.model_repo_commit)
    elif args.type == 'external':
        params['dockerfile'] = args.dockerfile
        params['repo'] = args.repo
        params['context'] = os.path.dirname(args.dockerfile)
    dockerfile = params.pop('dockerfile')
    tag = params.pop('tag')
    build(args, dockerfile, tag, top_level=True, **params)
