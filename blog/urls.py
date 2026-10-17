from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("posts", views.PostViewSet, basename="post")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("tags", views.TagViewSet, basename="tag")
router.register("comments", views.CommentModerationViewSet, basename="comment-moderation")

urlpatterns = [path("posts/<slug:slug>/comments/", views.PostCommentsView.as_view())] + router.urls