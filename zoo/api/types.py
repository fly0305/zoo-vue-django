from django.core.exceptions import ObjectDoesNotExist
import graphene
from graphene import relay
from graphene.types.json import JSONString

from ..analytics import models as analytics_models
from ..auditing import check_discovery
from ..auditing import models as auditing_models
from ..repos import models as repos_models
from ..services import models as services_models
from .paginator import Paginator
from .utils import CheckResultStatus

IssueStatusEnum = graphene.Enum.from_enum(auditing_models.Issue.Status)
IssueSeverityEnum = graphene.Enum.from_enum(check_discovery.Severity)
IssueEffortEnum = graphene.Enum.from_enum(check_discovery.Effort)


class Issue(graphene.ObjectType):
    repository = graphene.Field(lambda: Repository)
    kind_key = graphene.String()
    status = graphene.String()
    details = JSONString()
    remote_issue_id = graphene.Int()
    comment = graphene.String()
    last_check = graphene.String()

    class Meta:
        interfaces = (relay.Node,)

    @classmethod
    def from_db(cls, issue):
        return cls(
            id=issue.id,
            repository=issue.repository,
            kind_key=issue.kind_key,
            status=issue.status,
            details=issue.details,
            remote_issue_id=issue.remote_issue_id,
            comment=issue.comment,
            last_check=issue.last_check,
        )

    @classmethod
    def get_node(cls, info, issue_id):
        try:
            issue = auditing_models.Issue.objects.get(id=issue_id)
            return cls.from_db(issue)
        except ObjectDoesNotExist:
            return None


class IssueConnection(relay.Connection):
    total_count = graphene.Int()

    class Meta:
        node = Issue


class Service(graphene.ObjectType):
    owner = graphene.String()
    name = graphene.String()
    status = graphene.String()
    impact = graphene.String()
    datacenter = graphene.Field(lambda: DataCenter)
    repository = graphene.Field(lambda: Repository)
    slack_channel = graphene.String()
    pagerduty_url = graphene.String()
    dashboard_url = graphene.String()
    docs_url = graphene.String()
    health_check_url = graphene.String()

    @classmethod
    def from_db(cls, service):
        return cls(
            id=service.id,
            owner=service.owner,
            name=service.name,
            status=service.status,
            impact=service.impact,
            slack_channel=service.slack_channel,
            pagerduty_url=service.pagerduty_url,
            dashboard_url=service.dashboard_url,
            docs_url=service.docs_url,
            health_check_url=service.health_check_url,
            datacenter=service.datacenter_id,
            repository=service.repository_id,
        )

    @classmethod
    def get_node(cls, info, service_id):
        try:
            service = services_models.Service.objects.get(id=service_id)
            return cls.from_db(service)
        except ObjectDoesNotExist:
            return None

    def resolve_repository(self, info):
        try:
            return Repository.from_db(
                repos_models.Repository.objects.get(id=self.repository)
            )
        except ObjectDoesNotExist:
            return None

    def resolve_datacenter(self, info):
        try:
            return DataCenter.from_db(
                services_models.DataCenter.objects.get(id=self.datacenter)
            )
        except ObjectDoesNotExist:
            return None

    class Meta:
        interfaces = (relay.Node,)


class ServiceConnection(relay.Connection):
    total_count = graphene.Int()

    class Meta:
        node = Service


class Repository(graphene.ObjectType):
    remote_id = graphene.Int()
    owner = graphene.String()
    name = graphene.String()
    url = graphene.String()
    all_issues = relay.ConnectionField(IssueConnection)
    all_dependency_usages = relay.ConnectionField(lambda: DependencyUsageConnection)

    class Meta:
        interfaces = (relay.Node,)

    @classmethod
    def from_db(cls, repository):
        return cls(
            id=repository.id,
            remote_id=repository.remote_id,
            owner=repository.owner,
            name=repository.name,
            url=repository.url,
            all_issues=repository.issues,
        )

    @classmethod
    def get_node(cls, info, repository_id):
        try:
            repository = repos_models.Repository.objects.get(id=repository_id)
            return cls.from_db(repository)
        except ObjectDoesNotExist:
            return None

    def resolve_all_issues(self, info, **kwargs):
        paginator = Paginator(**kwargs)
        edges = []
        filtered_issues = auditing_models.Issue.objects.filter(repository_id=self.id)
        total = filtered_issues.count()
        page_info = paginator.get_page_info(total)

        for i, issue in enumerate(
            filtered_issues[
                paginator.slice_from : paginator.slice_to  # Ignore PEP8Bear
            ]
        ):
            cursor = paginator.get_edge_cursor(i + 1)
            node = Issue.from_db(issue)
            edges.append(IssueConnection.Edge(node=node, cursor=cursor))

        return IssueConnection(page_info=page_info, edges=edges, total_count=total)

    def resolve_all_dependency_usages(self, info, **kwargs):
        paginator = Paginator(**kwargs)
        edges = []
        filtered_dependencies = analytics_models.DependencyUsage.objects.filter(
            repo_id=self.id
        )
        total = filtered_dependencies.count()
        page_info = paginator.get_page_info(total)

        for i, dependency_usage in enumerate(
            filtered_dependencies[
                paginator.slice_from : paginator.slice_to  # Ignore PEP8Bear
            ]
        ):
            cursor = paginator.get_edge_cursor(i + 1)
            node = DependencyUsage.from_db(dependency_usage)
            edges.append(DependencyUsageConnection.Edge(node=node, cursor=cursor))

        return DependencyUsageConnection(
            page_info=page_info, edges=edges, total_count=total
        )


class RepositoryConnection(relay.Connection):
    total_count = graphene.Int()

    class Meta:
        node = Repository


class DataCenter(graphene.ObjectType):
    provider = graphene.String()
    region = graphene.String()

    class Meta:
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, datacenter_id):
        try:
            service = services_models.DataCenter.objects.get(id=datacenter_id)
            return cls.from_db(service)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def from_db(cls, datacenter):
        return cls(
            id=datacenter.id, provider=datacenter.provider, region=datacenter.region
        )


class Dependency(graphene.ObjectType):
    name = graphene.String()
    type = graphene.String()
    all_dependency_usages = relay.ConnectionField(lambda: DependencyUsageConnection)

    class Meta:
        interfaces = (relay.Node,)

    @classmethod
    def from_db(cls, dependency):
        return cls(id=dependency.id, name=dependency.name, type=dependency.type)

    def resolve_all_dependency_usages(self, info, **kwargs):
        paginator = Paginator(**kwargs)
        filtered_dependency_usages = analytics_models.DependencyUsage.objects.filter(
            dependency_id=self.id
        )
        total = filtered_dependency_usages.count()
        page_info = paginator.get_page_info(total)
        edges = []

        all_dependency_usages_type = self._meta.fields["all_dependency_usages"].type

        for i, dependency_usage in enumerate(
            filtered_dependency_usages[
                paginator.slice_from : paginator.slice_to  # Ignore PEP8Bear
            ]
        ):
            cursor = paginator.get_edge_cursor(i + 1)
            node = DependencyUsage.from_db(dependency_usage)
            edges.append(all_dependency_usages_type.Edge(node=node, cursor=cursor))

        return all_dependency_usages_type(
            page_info=page_info, edges=edges, total_count=total
        )

    @classmethod
    def get_node(cls, info, dependency_id):
        try:
            dependency = analytics_models.Dependency.objects.get(id=dependency_id)
            return cls.from_db(dependency)
        except ObjectDoesNotExist:
            return None


class DependencyConnection(relay.Connection):
    total_count = graphene.Int()

    class Meta:
        node = Dependency


class DependencyUsage(graphene.ObjectType):
    dependency = graphene.Field(lambda: Dependency)
    repository = graphene.Field(lambda: Repository)
    major_version = graphene.Int()
    minor_version = graphene.Int()
    patch_version = graphene.Int()
    for_production = graphene.String()
    version = graphene.String()

    class Meta:
        interfaces = (relay.Node,)

    @classmethod
    def from_db(cls, dependency_usage):
        return cls(
            id=dependency_usage.id,
            dependency=dependency_usage.dependency_id,
            repository=dependency_usage.repo_id,
            major_version=dependency_usage.major_version,
            minor_version=dependency_usage.minor_version,
            patch_version=dependency_usage.patch_version,
            for_production=dependency_usage.for_production,
            version=dependency_usage.version,
        )

    @classmethod
    def get_node(cls, info, dependency_usage_id):
        try:
            dependency_usage = analytics_models.DependencyUsage.objects.get(
                id=dependency_usage_id
            )
            return cls.from_db(dependency_usage)
        except ObjectDoesNotExist:
            return None

    def resolve_dependency(self, info):
        return Dependency.from_db(
            analytics_models.Dependency.objects.get(id=self.dependency)
        )

    def resolve_repository(self, info):
        return Repository.from_db(
            repos_models.Repository.objects.get(id=self.repository)
        )


class DependencyUsageConnection(relay.Connection):
    total_count = graphene.Int()

    class Meta:
        node = DependencyUsage


CheckResultStatusEnum = graphene.Enum.from_enum(CheckResultStatus)


class CheckResult(graphene.ObjectType):
    kind_key = graphene.String()
    is_found = graphene.Boolean()
    status = graphene.Field(CheckResultStatusEnum)
    severity = graphene.Field(IssueSeverityEnum)
    effort = graphene.Field(IssueEffortEnum)
    details = JSONString()
    title = graphene.String()
    description = graphene.String()

    @property
    def kind(self):
        return check_discovery.KINDS[self.kind_key]

    def resolve_severity(self, info):
        return self.kind.severity

    def resolve_effort(self, info):
        return self.kind.effort

    def resolve_title(self, info):
        return self.kind.title

    def resolve_description(self, info):
        return self.kind.format_description(self.details)
