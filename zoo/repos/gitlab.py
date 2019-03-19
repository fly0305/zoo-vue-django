from django.conf import settings
from gitlab import Gitlab, GitlabError, GitlabGetError, GitlabListError
import requests
from retry import retry

from .exceptions import MissingFilesError, RepositoryNotFoundError

gitlab = Gitlab(settings.GITLAB_URL, settings.GITLAB_TOKEN, api_version=4)

gitlab_retry = retry(
    (requests.RequestException, GitlabError), tries=5, delay=2, backoff=2
)


@gitlab_retry
def get_project(remote_id):
    try:
        project = gitlab.projects.get(remote_id)
    except GitlabGetError:
        raise RepositoryNotFoundError
    return project


@gitlab_retry
def download_archive(project, archive, sha=None):
    archive.seek(0)  # needed if retry
    try:
        project.repository_archive(sha=sha, streamed=True, action=archive.write)
    except GitlabListError:
        raise MissingFilesError
    return archive


@gitlab_retry
def get_repositories():
    for project in gitlab.projects.list(as_list=False):
        yield {
            "id": project.id,
            "provider": "gitlab",
            "owner": project.namespace["full_path"],
            "name": project.path,
            "url": project.web_url,
        }


@gitlab_retry
def get_project_details(remote_id):
    project = get_project(remote_id)
    return {
        "id": project.id,
        "name": project.name_with_namespace,
        "description": project.description,
        "avatar": project.avatar_url,
        "url": project.web_url,
        "readme": project.readme_url,
        "stars": project.star_count,
        "forks": project.forks_count,
        "branch_count": project.branches.list(as_list=False).total,
        "member_count": project.members.list(as_list=False).total,
        "issue_count": project.issues.list(as_list=False).total,
        "last_activity_at": project.last_activity_at,
    }


@gitlab_retry
def get_languages(remote_id):
    project = get_project(remote_id)
    try:
        langs = project.languages()
    except GitlabGetError:
        return {}
    return langs


@gitlab_retry
def create_remote_issue(issue, user_name, reverse_url):
    gitlab_issue = issue.repository.remote_git_object.issues.create(
        {
            "title": f"{issue.kind.category}: {issue.kind.title}",
            "description": issue.description_md
            + (
                "\n\n---\n\n"
                f"severity: {issue.kind.severity.value} ; effort: {issue.kind.effort.value} "
                f"*This issue was created by @{user_name} "
                f"via [The Zoo]({reverse_url})*"
            ),
        }
    )

    return gitlab_issue.iid


@gitlab_retry
def create_remote_commit(remote_id, message, actions, branch, **kwargs):
    """Create a new commit in a remote Gitlab repository.

    :param remote_id: ID of the remote repository.
    :param message: The commit message.
    :param actions: List of actions to perform in the commit.
    :param branch: Name of the branch where to commit the actions.
    """
    start_branch = kwargs.get("start_branch", "master")

    project = get_project(remote_id)
    commit = project.commits.create(
        {
            "commit_message": message,
            "actions": actions,
            "branch": branch,
            "start_branch": start_branch,
        }
    )
    return commit.get_id()


@gitlab_retry
def create_merge_request(remote_id, title, source_branch, **kwargs):
    """Create a new merge request in a remote Gitlab repository.

    :param remote_id: ID of the remote repository.
    :param title: Title of the merge request.
    :param source_branch: Branch containing the changes.
    """
    target_branch = kwargs.get("target_branch", "master")
    description = kwargs.get("description", "")
    reverse_url = kwargs.get("reverse_url", None)

    project = get_project(remote_id)

    description += "\n\n---\n\n" if description else ""
    description += f"*via [The Zoo]({reverse_url})*" if reverse_url else "*via The Zoo*"

    merge_request = project.mergerequests.create(
        {
            "title": title,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "description": description,
        }
    )
    return merge_request.get_id()
