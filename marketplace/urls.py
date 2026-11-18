from django.urls import path

from . import views


app_name = "marketplace"

urlpatterns = [
    path("admin/", views.admin_panel, name="admin_panel"),
    path("admin/courses/", views.course_list, name="course_list"),
    path("admin/courses/new/", views.course_create, name="course_create"),
    path("admin/courses/<int:pk>/edit/", views.course_update, name="course_update"),
    path("admin/courses/<int:pk>/delete/", views.course_delete, name="course_delete"),
    path("marketplace/", views.listing_catalog, name="listing_catalog"),
    path("marketplace/mine/", views.my_listings, name="my_listings"),
    path("marketplace/listings/new/", views.listing_create, name="listing_create"),
    path("marketplace/listings/<int:pk>/", views.listing_detail, name="listing_detail"),
    path("marketplace/listings/<int:pk>/edit/", views.listing_update, name="listing_update"),
    path("marketplace/listings/<int:pk>/delete/", views.listing_delete, name="listing_delete"),
    path("marketplace/listings/<int:pk>/status/", views.listing_update_status, name="listing_update_status"),
    path("marketplace/moderation/", views.listing_moderation, name="listing_moderation"),
    path("marketplace/moderation/<int:pk>/remove/", views.listing_remove, name="listing_remove"),
]
