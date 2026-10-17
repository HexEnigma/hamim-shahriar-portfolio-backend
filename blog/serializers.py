from rest_framework import serializers

from core.serializers import ResolveMixin
from portfolio.models import Profile

from .models import Category, Comment, Post, PostLike, Tag


class CategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "posts_count"]
        read_only_fields = ["slug"]

    def get_posts_count(self, obj):
        value = getattr(obj, "posts_count", None)
        return value if value is not None else obj.posts.filter(status=Post.Status.PUBLISHED).count()


class TagSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "posts_count"]
        read_only_fields = ["slug"]

    def get_posts_count(self, obj):
        value = getattr(obj, "posts_count", None)
        return value if value is not None else obj.posts.filter(status=Post.Status.PUBLISHED).count()


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class TagMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class PostListSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer(read_only=True)
    tags = TagMiniSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ["id", "title", "slug", "excerpt", "cover_image", "cover_image_url", "category", "tags", "status", "published_at",
                  "views_count", "reading_time", "is_featured", "likes_count", "comments_count", "created_at"]


class PostDetailSerializer(PostListSerializer):
    author_name = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ["content", "author_name", "is_liked", "related_posts", "updated_at"]

    def get_author_name(self, obj):
        return Profile.get_solo().full_name

    def get_is_liked(self, obj):
        visitor = self.context["request"].headers.get("X-Visitor-Id", "").strip()
        return bool(visitor) and PostLike.objects.filter(post=obj, visitor_id=visitor).exists()

    def get_related_posts(self, obj):
        if not obj.category_id:
            return []
        qs = (Post.objects.with_counts().published().filter(category_id=obj.category_id).exclude(pk=obj.pk)
              .select_related("category").prefetch_related("tags").order_by("-published_at")[:3])
        return PostListSerializer(qs, many=True, context=self.context).data


class PostWriteSerializer(ResolveMixin, serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)

    class Meta:
        model = Post
        fields = ["title", "excerpt", "content", "cover_image", "cover_image_url", "category", "tags", "status", "is_featured"]

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value.strip()

    def validate(self, attrs):
        if self.resolve(attrs, "status", Post.Status.DRAFT) == Post.Status.PUBLISHED:
            errors = {}
            if len((self.resolve(attrs, "content", "") or "").strip()) < 100:
                errors["content"] = "A post needs at least 100 characters before it can be published."
            if self.resolve(attrs, "category") is None:
                errors["category"] = "Choose a category before publishing."
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class ReplySerializer(serializers.ModelSerializer):          # public: no email
    class Meta:
        model = Comment
        fields = ["id", "name", "website", "content", "created_at"]


class PublicCommentSerializer(ReplySerializer):
    replies = ReplySerializer(source="approved_replies", many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "name", "website", "content", "created_at", "replies"]


class CommentCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=2, max_length=120,
                                 error_messages={"min_length": "Name must be at least 2 characters."})
    content = serializers.CharField(min_length=5, max_length=1000,
                                    error_messages={"min_length": "Comment must be at least 5 characters.",
                                                    "max_length": "Comment must be 1000 characters or fewer."})
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True,
                                                error_messages={"does_not_exist": "Invalid parent comment."})

    class Meta:
        model = Comment
        fields = ["name", "email", "website", "content", "parent"]

    def validate_parent(self, parent):
        if parent is None:
            return parent
        post = self.context["post"]
        if parent.post_id != post.id or parent.parent_id is not None or not parent.is_approved:
            raise serializers.ValidationError("Invalid parent comment.")
        return parent


class ModerationCommentSerializer(serializers.ModelSerializer):   # owner only
    post_title = serializers.CharField(source="post.title", read_only=True)
    post_slug = serializers.CharField(source="post.slug", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "post_title", "post_slug", "name", "email", "website", "content", "parent",
                  "is_approved", "created_at"]
        read_only_fields = ["name", "email", "website", "content", "parent", "created_at"]