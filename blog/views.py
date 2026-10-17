import hashlib

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.pagination import CommentPagination, PostPagination
from core.permissions import IsOwner, is_owner
from core.throttles import CommentThrottle, LikeThrottle
from core.utils import client_ip

from .filters import CommentFilter, PostFilter
from .models import Category, Comment, Post, PostLike, Tag
from .serializers import (CategorySerializer, CommentCreateSerializer, ModerationCommentSerializer,
                          PostDetailSerializer, PostListSerializer, PostWriteSerializer,
                          PublicCommentSerializer, TagSerializer)


def base_posts():
    return Post.objects.with_counts().select_related("category", "author").prefetch_related("tags").order_by("-published_at", "-created_at")
class PostViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    lookup_value_regex = r"[-\w]+"
    pagination_class = PostPagination
    filterset_class = PostFilter
    search_fields = ["title", "excerpt", "content"]
    ordering_fields = ["published_at", "views_count", "likes_count", "title"]

    def get_queryset(self):
        qs = base_posts()
        if not is_owner(self.request.user):
            return qs.published()                     # visitors never see drafts
        if self.action == "list":
            param = self.request.query_params.get("status", "").upper()
            if param == "ALL":
                return qs
            if param in Post.Status.values:
                return qs.filter(status=param)
            return qs.published()
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostWriteSerializer

    def _detail(self, post):
        fresh = base_posts().get(pk=post.pk)
        return PostDetailSerializer(fresh, context=self.get_serializer_context()).data

    def create(self, request, *args, **kwargs):
        s = PostWriteSerializer(data=request.data, context=self.get_serializer_context())
        s.is_valid(raise_exception=True)
        post = s.save(author=request.user)
        return Response(self._detail(post), status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        s = PostWriteSerializer(self.get_object(), data=request.data, partial=partial,
                                context=self.get_serializer_context())
        s.is_valid(raise_exception=True)
        return Response(self._detail(s.save()))

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        if post.status == Post.Status.PUBLISHED and not is_owner(request.user):
            self._count_view(request, post)
        return Response(self.get_serializer(post).data)

    def _count_view(self, request, post):
        """One view per visitor per cooldown window; atomic F() update."""
        ident = request.headers.get("X-Visitor-Id", "").strip() or f"ip:{client_ip(request)}"
        key = f"post-view:{post.pk}:{hashlib.sha1(ident.encode()).hexdigest()}"
        if cache.add(key, 1, settings.VIEW_COOLDOWN_SECONDS):
            Post.objects.filter(pk=post.pk).update(views_count=F("views_count") + 1)
            post.refresh_from_db(fields=["views_count"])

    @action(detail=True, methods=["post"], permission_classes=[AllowAny], throttle_classes=[LikeThrottle])
    def like(self, request, slug=None):
        visitor = request.headers.get("X-Visitor-Id", "").strip()
        if not visitor or len(visitor) > 64:
            return Response({"detail": "A valid X-Visitor-Id header is required."}, status=400)
        post = self.get_object()
        with transaction.atomic():
            like, created = PostLike.objects.get_or_create(
                post=post, visitor_id=visitor, defaults={"ip_address": client_ip(request)})
            if not created:
                like.delete()
        return Response({"liked": created, "likes_count": post.likes.count()})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(
        posts_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED))).order_by("name")
    serializer_class = CategorySerializer
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.annotate(
        posts_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED))).order_by("name")
    serializer_class = TagSerializer
    pagination_class = None


class PostCommentsView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    pagination_class = CommentPagination

    def get_post(self):
        return get_object_or_404(Post.objects.published(), slug=self.kwargs["slug"])

    def get_queryset(self):
        replies = Comment.objects.filter(is_approved=True).order_by("created_at")
        return (Comment.objects.filter(post=self.get_post(), is_approved=True, parent__isnull=True)
                .prefetch_related(Prefetch("replies", queryset=replies, to_attr="approved_replies"))
                .order_by("-created_at"))

    def get_serializer_class(self):
        return CommentCreateSerializer if self.request.method == "POST" else PublicCommentSerializer

    def get_throttles(self):
        return [CommentThrottle()] if self.request.method == "POST" else super().get_throttles()

    def create(self, request, *args, **kwargs):
        post = self.get_post()
        s = self.get_serializer(data=request.data, context={**self.get_serializer_context(), "post": post})
        s.is_valid(raise_exception=True)
        s.save(post=post, is_approved=False)
        return Response({"detail": "Your comment is awaiting approval.", "is_approved": False}, status=201)


class CommentModerationViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    permission_classes = [IsOwner]
    queryset = Comment.objects.select_related("post").order_by("is_approved", "-created_at")
    serializer_class = ModerationCommentSerializer
    pagination_class = CommentPagination
    filterset_class = CommentFilter
    http_method_names = ["get", "patch", "delete", "head", "options"]