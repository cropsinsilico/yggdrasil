import os
import argparse
import subprocess
import json
import urllib.request
_utils_dir = os.path.dirname(__file__)


def build(dockerfile, tag, flags=[], repo='cropsinsilico/yggdrasil',
          context=_utils_dir, disable_latest=False):
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
        disable_latest (bool, optional): If True, the new image will not
            be tagged 'latest' in addition to the provided tag value. Defaults
            to False.

    """
    args = ['docker', 'build', '-t', f'{repo}:{tag}', '-f', dockerfile] + flags
    args.append(context)
    subprocess.call(args)
    if not disable_latest:
        args = ['docker', 'tag', f'{repo}:{tag}', f"{repo}:latest"]
        subprocess.call(args)


def push_image(tag, repo='cropsinsilico/yggdrasil'):
    r"""Push a docker image to DockerHub.

    Args:
        tag (str): Tag that should be added to the image.
        repo (str, optional): DockerHub repository that the image will be
            pushed to. Defaults to 'cropsinsilico/yggdrasil'.

    """
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
    # dockerfile = os.path.join(_utils_dir, 'release.Docker')
    # flags = ['--build-arg', f'version={version}']
    repo = 'cropsinsilico/yggdrasil'
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


def params_commit(commit):
    r"""Get parameters to build a docker image containing a version of
    yggdrasil specific to a commit.

    Args:
        commit (str): ID for commit to install from the yggdrasil git repo.

    Returns:
        dict: Docker build parameters.

    """
    dockerfile = os.path.join(_utils_dir, 'commit.Docker')
    tag = commit
    flags = ['--build-arg', f'commit={commit}']
    repo = 'cropsinsilico/yggdrasil-dev'
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


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
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


def params_service(params):
    r"""Get parameters to build a docker image containing a version of
    yggdrasil sepcific to a commit or tagged release that runs an yggdrasil
    integration service manager.

    Args:
        params (dict): Docker build parameters set based on the base type.

    Returns:
        dict: Docker build parameters.

    """
    dockerfile = os.path.join(_utils_dir, 'service.Docker')
    repo = params["repo"]
    tag = params["tag"]
    flags = ['--build-arg', f'base={repo}:{tag}']
    repo = repo.replace('yggdrasil', 'yggdrasil-service')
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


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
    args = parser.parse_args()
    if args.commit:
        params = params_commit(args.commit)
    else:
        params = params_release(args.version)
    if args.type == 'executable':
        params = params_executable(params)
    elif args.type == 'service':
        params = params_service(params)
    params.setdefault('disable_latest', args.disable_latest)
    dockerfile = params.pop('dockerfile')
    tag = params.pop('tag')
    build(dockerfile, tag, **params)
    if args.push:
        push_image(tag, repo=params['repo'])
        if not params['disable_latest']:
            push_image('latest', repo=params['repo'])
