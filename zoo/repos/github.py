from django.conf import settings
from github import Github, GithubException, InputGitTreeElement
from github.GithubException import UnknownObjectException
from github.GithubObject import NotSet
import requests
from retry import retry

from .exceptions import MissingFilesError, RepositoryNotFoundError

github = Github(settings.GITHUB_TOKEN)

github_retry = retry(
    (requests.RequestException, GithubException), tries=5, delay=2, backoff=2
)


@github_retry
def get_repositories():
    for repo in github.get_user().get_repos():
        yield {
            "id": repo.id,
            "provider": "github",
            "owner": repo.owner.login,
            "name": repo.name,
            "url": repo.svn_url,
        }


@github_retry
def get_project(github_id):
    try:
        project = github.get_repo(github_id)
    except UnknownObjectException:
        raise RepositoryNotFoundError
    return project


@github_retry
def download_archive(project, archive, sha=None):
    archive.seek(0)  # needed if retry
    sha = sha if sha else NotSet
    archive_url = project.get_archive_link("tarball", ref=sha)
    r = requests.get(archive_url, stream=True)
    if r.status_code == requests.codes.not_found:
        raise MissingFilesError
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            archive.write(chunk)
    return archive


@github_retry
def get_project_details(github_id):
    project = get_project(github_id)
    return {
        "id": project.id,
        "name": project.full_name,
        "description": project.description,
        "avatar": None,
        "url": project.svn_url,
        "readme": project.get_readme().url,
        "stars": project.stargazers_count,
        "forks": project.forks_count,
        "branch_count": project.get_branches().totalCount,
        "member_count": project.get_contributors().totalCount,
        "issue_count": project.get_issues().totalCount,
        "last_activity_at": project.updated_at,
    }


@github_retry
def get_languages(remote_id):
    langs = get_project(remote_id).get_languages()
    sum_of_bytes = sum(langs.values())
    langs_percent = {}
    for lang, num in langs.items():
        langs_percent[lang] = round(num / sum_of_bytes * 100, 2)
    return langs_percent


@github_retry
def create_remote_issue(issue, user_name, reverse_url):
    github_issue = issue.repository.remote_git_object.create_issue(
        title=f"{issue.kind.category}: {issue.kind.title}",
        body=issue.description_md
        + (
            "\n\n---\n\n"
            f"severity: {issue.kind.severity.value} ; effort: {issue.kind.effort.value} "
            f"*This issue was created by @{user_name} "
            f"via [The Zoo]({reverse_url})*"
        ),
    )

    return github_issue.number


@github_retry
def create_remote_commit(remote_id, message, actions, branch, **kwargs):
    """Create a new commit in a remote GitHub repository.

    See the following link for details on the implementation using the GitHub
    API: http://www.levibotelho.com/development/commit-a-file-with-the-github-api/

    :param remote_id: ID of the remote repository.
    :param message: The commit message.
    :param actions: List of actions to perform in the commit.
    :param branch: Name of the branch where to commit the actions.
    """
    start_branch = kwargs.get("start_branch", "master")

    project = get_project(remote_id)
    ref = project.get_git_ref(f"heads/{start_branch}")
    commit = project.get_git_commit(ref.object.sha)

    if {action["action"] for action in actions} & {"move", "delete"}:
        new_tree = _create_new_tree(project, actions, commit.tree)
    else:
        new_tree = _update_tree(project, actions, commit.tree)

    new_commit = project.create_git_commit(
        message=message, parents=[commit], tree=new_tree
    )
    project.create_git_ref(ref=f"refs/heads/{branch}", sha=new_commit.sha)
    return new_commit.sha


@github_retry
def create_merge_request(remote_id, title, source_branch, **kwargs):
    """Create a new pull request in a remote GitHub repository.

    :param remote_id: ID of the remote repository.
    :param title: Title of the pull request.
    :param source_branch: Branch containing the changes.
    """
    target_branch = kwargs.get("target_branch", "master")
    description = kwargs.get("description", "")
    reverse_url = kwargs.get("reverse_url", None)

    project = get_project(remote_id)

    description += "\n\n---\n\n" if description else ""
    description += f"*via [The Zoo]({reverse_url})*" if reverse_url else "*via The Zoo*"

    pull = project.create_pull(
        title=title, head=source_branch, base=target_branch, body=description
    )
    return pull.number


def _create_tree_element(path, type="blob", mode="100644", **kwargs):
    return InputGitTreeElement(path=path, type=type, mode=mode, **kwargs)


def _create_new_tree(project, actions, tree):
    tree_dict = {}
    full_tree = project.get_git_tree(tree.sha, recursive=True).tree

    for tree_elem in full_tree:
        if tree_elem.type == "tree":
            continue

        tree_dict[tree_elem.path] = _create_tree_element(
            path=tree_elem.path,
            sha=tree_elem.sha,
            mode=tree_elem.mode,
            type=tree_elem.type,
        )

    for action in actions:
        action_name = action["action"]

        if action_name in ["create", "update"]:
            tree_dict[action["file_path"]] = _create_tree_element(
                path=action["file_path"], content=action["content"]
            )

        elif action_name == "move":
            tree_elem = tree_dict.pop(action["previous_path"])
            elem_data = dict(tree_elem._identity)
            elem_data["path"] = action["file_path"]
            tree_dict[elem_data["path"]] = _create_tree_element(**elem_data)

        elif action_name == "delete":
            tree_dict.pop(action["file_path"])

    return project.create_git_tree(list(tree_dict.values()))


def _update_tree(project, actions, tree):
    tree_list = [
        _create_tree_element(action["file_path"], content=action["content"])
        for action in actions
    ]
    return project.create_git_tree(tree_list, base_tree=tree)
