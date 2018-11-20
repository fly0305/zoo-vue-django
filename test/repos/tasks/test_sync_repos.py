import pytest
from faker import Faker
from unittest.mock import patch
from zoo.repos.models import Repository, Provider
from zoo.repos.tasks import sync_repos

pytestmark = pytest.mark.django_db


class FakeGitProject:
    def __init__(self, pid):
        self.fake = Faker()
        self.id = self.fake.pyint() if pid is None else pid


class FakeGitlabProject(FakeGitProject):
    def __init__(self, pid, owner, name, url):
        super().__init__(pid)
        self.namespace = {"full_path": self.fake.word() if owner is None else owner}
        self.path = self.fake.word() if name is None else name
        self.web_url = self.fake.url() if url is None else url


class FakeGithubProject(FakeGitProject):
    def __init__(self, pid, owner, name, url):
        super().__init__(pid)

        class FakeOwner:
            def __init__(self, login):
                self.login = login

        login = owner if owner else self.fake.word()
        self.owner = FakeOwner(login)
        self.name = self.fake.word() if name is None else name
        self.svn_url = self.fake.url() if url is None else url


def generate_project_list(pid=None, owner=None, name=None, url=None, **kwargs):
    return {
        "gitlab": [FakeGitlabProject(pid, owner, name, url)],
        "github": [FakeGithubProject(pid + 1, owner, name, url)],
    }


def test_sync_untouched_repo(repository):
    project_list = generate_project_list(
        repository.remote_id, repository.owner, repository.name, repository.url
    )
    with patch(
        "gitlab.v4.objects.ProjectManager.list", return_value=project_list["gitlab"]
    ), patch(
        "github.AuthenticatedUser.AuthenticatedUser.get_repos",
        return_value=project_list["github"],
    ):
        sync_repos()

    gitlab_project = project_list["gitlab"][0]
    assert gitlab_project.id == repository.remote_id
    assert gitlab_project.namespace["full_path"] == repository.owner
    assert gitlab_project.path == repository.name
    assert gitlab_project.web_url == repository.url

    github_project = project_list["github"][0]
    assert github_project.id == repository.remote_id + 1
    assert github_project.owner.login == repository.owner
    assert github_project.name == repository.name
    assert github_project.svn_url == repository.url


def test_sync_moved_repo(repository):
    project_list = generate_project_list(repository.remote_id)
    with patch(
        "gitlab.v4.objects.ProjectManager.list", return_value=project_list["gitlab"]
    ), patch(
        "github.AuthenticatedUser.AuthenticatedUser.get_repos",
        return_value=project_list["github"],
    ):
        sync_repos()

    gitlab_project = project_list["gitlab"][0]
    repository = Repository.objects.get(
        remote_id=gitlab_project.id, provider=Provider.GITLAB.value
    )
    assert gitlab_project.namespace["full_path"] == repository.owner
    assert gitlab_project.path == repository.name
    assert gitlab_project.web_url == repository.url

    github_project = project_list["github"][0]
    repository = Repository.objects.get(
        remote_id=github_project.id, provider=Provider.GITHUB.value
    )
    assert github_project.owner.login == repository.owner
    assert github_project.name == repository.name
    assert github_project.svn_url == repository.url
