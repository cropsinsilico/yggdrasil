import os
import argparse
import subprocess
import urllib.request
import json


def get_latest_tag():
    r"""Get the highest tag.

    Returns:
        str: Highest tag.

    """
    url = ("https://registry.hub.docker.com/v2/repositories/cropsinsilico/"
           "yggdrasil-executable/tags")
    response = urllib.request.urlopen(url)
    results = json.loads(response.read())['results']
    tag = max(results, key=lambda x: x['name'])['name']
    return tag


def run(yamls, additional_flags, tag=None, pull=False, show_help=False):
    r"""Call docker run with the appropriate volumes required to capture the
    YAML specification files.

    Args:
        yamls (list): YAML specification files.
        additional_flags (list): Additional CLI flags that should be passed to
            yggrun via the executable docker container.
        tag (str, optional): Docker image tag that should be used. Defaults to
            None and the latest image will be used.
        pull (bool, optional): If True the Docker image will be pulled first.
            Defaults to False.
        show_help (bool, optional): If True, the help information for the CLI
            will be displayed. Defaults to False.

    """
    if tag is None:
        tag = get_latest_tag()
    image = f'cropsinsilico/yggdrasil-executable:{tag}'
    # TODO: Load the YAMLs and check for model directories?
    yamls_parsed = []
    volumes = []
    for x in yamls:
        if x.startswith('git:'):
            yamls_parsed.append(x)
            continue
        if not os.path.isabs(x):
            x = os.path.abspath(x)
        vdir, xbase = os.path.split(x)
        vmnt = '/' + os.path.basename(vdir)
        if (vdir, vmnt) not in volumes:
            volumes.append((vdir, vmnt))
        yamls_parsed.append(os.path.join(vmnt, xbase))
    args = ['docker', 'run', '-it']
    for vdir, vmnt in volumes:
        args.append(f'--volume={vdir}:{vmnt}')
    args += [image] + yamls_parsed + additional_flags
    if show_help:
        args += ["-h"]
    if pull:
        subprocess.call(["docker", "pull", image])
    subprocess.call(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Run an integration using the yggdrasil executable Docker image.")
    parser.add_argument(
        "yamlfile", nargs="+",
        help="One or more yaml specification files.")
    parser.add_argument(
        "--docker-tag", type=str,
        help=("Tag for the yggdrasil executable Docker image that should be "
              "called."))
    parser.add_argument(
        "--pull-docker-image", action="store_true",
        help="Pull the yggdrasil executable Docker image before running it.")
    parser.add_argument(
        "--help-run", action="store_true",
        help="Print the help for the yggrun CLI.")
    args, extra = parser.parse_known_args()
    run(args.yamlfile, extra, tag=args.docker_tag,
        pull=args.pull_docker_image, show_help=args.help_run)
