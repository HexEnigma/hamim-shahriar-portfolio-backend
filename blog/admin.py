from django.contrib import admin

from .models import Category, Comment, Post, PostLike, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "category", "published_at", "views_count", "is_featured")
    search_fields = ("title", "excerpt", "content")
    list_filter = ("status", "category", "tags", "is_featured")
    readonly_fields = ("slug", "published_at", "reading_time", "views_count")
    exclude = ("author",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("post", "visitor_id", "ip_address", "created_at")
    list_filter = ("created_at",)
    search_fields = ("post__title", "visitor_id")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "post", "is_approved", "parent", "created_at")
    search_fields = ("name", "email", "content")
    list_filter = ("is_approved",)
    actions = ["approve"]

    @admin.action(description="Approve selected comments")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)