"""Libraries URL Configuration."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.LibraryList.as_view(), name="library_list"),
    path(
        "<str:owner_slug>/<str:name_slug>",
        views.LibraryDetail.as_view(),
        name="library_detail",
    ),
    path(
        "<str:owner_slug>/<str:name_slug>/update",
        views.LibraryUpdate.as_view(),
        name="library_update",
    ),
    path(
        "<str:owner_slug>/<str:name_slug>/delete",
        views.LibraryDelete.as_view(),
        name="library_delete",
    ),
    path("new", views.LibraryCreate.as_view(), name="library_create"),
]
