import os
import json
import argparse
from github import Github
from yggdrasil import __version__
from yggdrasil.schema import get_model_form_schema


def update_schema(token):
    r"""Update the model form schema via pull request to the
    cropsinsilico/model_submission_form repository.

    Args:
        token (str): Github authentication token that should be used.

    """
    contents = json.dumps(get_model_form_schema(), indent='    ')
    ver = __version__
    repo_name = "cropsinsilico/model_submission_form"
    msg = f"Update model form schema to version for yggdrasil {ver}"
    branch = f"schema-update-{ver}"
    schema = "model_submission_form/static/model.json"
    gh = Github(token)
    repo = gh.get_repo(repo_name)
    main = repo.get_branch('main')
    schema_sha = repo.get_contents(schema).sha
    repo.create_git_ref(f"refs/heads/{branch}", main.commit.sha)
    repo.update_file(schema, msg, contents, schema_sha, branch=branch)
    repo.create_pull(title=f"Update schema to {ver}",
                     body=msg, head=branch, base="main")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Update the model form schema via pull request to the"
        "cropsinsilico/model_submission_form repository.")
    parser.add_argument(
        '--token',
        help=("Github authentication token that should be used to open the "
              "pull request. The token must have write access to the "
              "cropsinsilico/model_submission_form repository."))
    args = parser.parse_args()
    if args.token is None:
        args.token = os.environ.get('YGGDRASIL_UPDATE_TOKEN', None)
    assert(args.token)
    update_schema = update_schema(args.token)
