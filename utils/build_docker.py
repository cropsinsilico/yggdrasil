import os
import argparse
import subprocess
_utils_dir = os.path.dirname(__file__)


def build(dockerfile, tag, flags=[], repo='cropsinsilico/yggdrasil',
          context='.'):
    r"""Build a docker image.

    Args:
        dockerfile (str): Full path to the docker file that should be used.
        tag (str): Tag that should be added to the image.
        flags (list, optional): Additional flags that should be passed to
            the build command. Defaults to [].
        repo (str, optional): DockerHub repository that the image will be
            pushed to. Defaults to 'cropsinsilico/yggdrasil'.
        context (str, optional): Directory that should be provided as the
            context for the image. Defaults to '.'.

    """
    args = ['docker', 'build', '-t', f'{repo}:{tag}', '-f', dockerfile] + flags
    args.append(context)
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
    r"""Build a docker image containing an yggdrasil release.

    Args:
        version (str): Release version to install in the image.

    Returns:
        dict: Docker build parameters.

    """
    dockerfile = os.path.join(_utils_dir, 'commit.Docker')
    # dockerfile = os.path.join(_utils_dir, 'release.Docker')
    tag = f'v{version}'
    flags = ['--build-arg', f'commit=tags/v{version}']
    # flags = ['--build-arg', f'version={version}']
    repo = 'cropsinsilico/yggdrasil'
    return dict(dockerfile=dockerfile, tag=tag, flags=flags, repo=repo)


def params_commit(commit):
    r"""Build a docker image containing a version of yggdrasil specific to a
    commit.

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


def build_executable(params):
    r"""Build a docker image containing a version of yggdrasil specific to a
    commit or tagged release that can be used as an executable.

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Build a docker image containing a version of yggdrasil.")
    subparsers = parser.add_subparsers(
        dest="type",
        help="Type of docker image that should be built.")
    parser_rel = subparsers.add_parser(
        "release", help="Build a docker image containing tagged release.")
    parser_rel.add_argument(
        "version", type=str,
        help="Release version that should be installed in the image.")
    parser_com = subparsers.add_parser(
        "commit", help="Build a docker image containing a specific commit.")
    parser_com.add_argument(
        "commit", type=str,
        help="Commit ID that should be installed in the image.")
    joint_args = [
        (("--push", ),
         {"action": "store_true",
          "help": ("After successfully building the image, push it to "
                   "DockerHub.")}),
        (("--executable", ),
         {"action": "store_true",
          "help": ("Build the image so that it can be used as an "
                   "executable.")})]
    for iparser in [parser_rel, parser_com]:
        for ia, ik in joint_args:
            iparser.add_argument(*ia, **ik)
    args = parser.parse_args()
    if args.type == 'release':
        params = params_release(args.version)
    elif args.type == 'commit':
        params = params_commit(args.commit)
    if args.executable:
        params = build_executable(params)
    dockerfile = params.pop('dockerfile')
    tag = params.pop('tag')
    build(dockerfile, tag, **params)
    if args.push:
        push_image(tag, repo=params['repo'])
