import os
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


def build(dockerfile=None, tag=None, flags=[],
          repo='cropsinsilico/yggdrasil', context=_utils_dir, cwd=None,
          base=None, args=None):
    r"""Build a docker image.

    Args:
        dockerfile (str): Full path to the docker file that should be used.
        tag (str): Tag that should be added to the image.
        flags (list, optional): Additional flags that should be passed to
            the build command. Defaults to [].
        repo (str, optional): DockerHub repository that the image will be
            pushed to. Defaults to 'cropsinsilico/yggdrasil'.
        context (str, optional): Directory that should be provided as the
            context for the image. Defaults to the directory containing this
            script.
        base (dict, optional): Parameters for the base image.
        args (ParsedArgs, optional): Parsed arguments.

    """
    # TODO: Update so multiple targets are built
    # https://docs.docker.com/build/building/multi-platform/
    # TODO: Update sysv_ipc & czmq to have linux/aarch64 builds
    if base:
        base_tag = f"{base['repo']}:{base['tag']}"
        if not image_exists(base_tag):
            build(args=args, **base)
    assert args and args.python
    flags = flags + ['--build-arg', f'python={args.python}']
    if args.verbose:
        flags += ['--progress', 'plain']
    if repo:
        assert tag
        docker_tag = f'{repo}:{tag}'
    else:
        assert tag
        docker_tag = tag
    args = ['docker', 'build', '-t', docker_tag, '-f', dockerfile,
            '--platform', 'linux/amd64'] + flags
    args.append(context)
    subprocess.call(args)
    if not args.disable_latest:
        assert repo
        args = ['docker', 'tag', docker_tag, f"{repo}:latest"]
        subprocess.call(args, cwd=cwd)


def push_image(tag, repo='cropsinsilico/yggdrasil'):
    r"""Push a docker image to DockerHub.

    Args:
        tag (str): Tag that should be added to the image.
        repo (str, optional): DockerHub repository that the image will be
            pushed to. Defaults to 'cropsinsilico/yggdrasil'.

    """
    assert repo and tag
    args = ['docker', 'push', f'{repo}:{tag}']
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
    flags = ['--build-arg', f'base={repo}:{tag}']
    repo = repo.replace('yggdrasil', 'yggdrasil-executable')
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo,
                base=params)


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
        base = repo.replace('yggdrasil', 'yggdrasil-service')
        base_params = params_service(params)
        repo = repo.replace('yggdrasil', 'yggdrasil-loaded-service')
        dockerfile = os.path.join(_utils_dir, 'loaded_service.Docker')
        if model_repo_commit == 'latest':
            url = ("https://api.github.com/repos/cropsinsilico/"
                   "yggdrasil_models/commits/main")
            response = json.loads(urllib.request.urlopen(url).read())
            model_repo_commit = response['sha']
    else:
        base = repo
        base_params = params
        repo = repo.replace('yggdrasil', 'yggdrasil-service')
        dockerfile = os.path.join(_utils_dir, 'service.Docker')
    flags = ['--build-arg', f'base={base}:{tag}']
    if model_repo_commit:
        tag += f'-{model_repo_commit}'
        flags += ['--build-arg', f'commit={model_repo_commit}']
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo,
                base=base_params)


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
        "--verbose", "-v", action="store_true",
        help="Show build output")
    parser.add_argument(
        "--push", action="store_true",
        help="After successfully building the image, push it to DockerHub.")
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
    # else:
    dockerfile = params.pop('dockerfile')
    tag = params.pop('tag')
    build(dockerfile, tag, args=args, **params)
    if args.push:
        assert not params['repo'].endswith('-local')
        push_image(tag, repo=params['repo'])
        if not args.disable_latest:
            push_image('latest', repo=params['repo'])
