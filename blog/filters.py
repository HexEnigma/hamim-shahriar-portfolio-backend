from django_filters import rest_framework as filters

from .models import Comment, Post


class PostFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category__slug")
    tag = filters.CharFilter(field_name="tags__slug")

    class Meta:
        model = Post
        fields = ["is_featured"]


class CommentFilter(filters.FilterSet):
    post = filters.CharFilter(field_name="post__slug")

    class Meta:
        model = Comment
        fields = ["is_approved"]