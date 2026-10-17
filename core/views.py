from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from blog.models import Comment, Post, PostLike
from portfolio.models import ContactMessage, Project, Skill

from .permissions import IsOwner
from .throttles import LoginThrottle

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_superuser"]


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            raise AuthenticationFailed("Invalid credentials.") from None
        data["user"] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [LoginThrottle]


class LogoutView(APIView):
    permission_classes = [IsOwner]

    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh", "")).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Logged out."})


class MeView(APIView):
    permission_classes = [IsOwner]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value


class ChangePasswordView(APIView):
    permission_classes = [IsOwner]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        request.user.set_password(s.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password changed."})


class DashboardStatsView(APIView):
    permission_classes = [IsOwner]

    def get(self, request):
        posts = Post.objects.aggregate(
            total=Count("id"),
            published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
            draft=Count("id", filter=Q(status=Post.Status.DRAFT)),
            views=Sum("views_count"),
        )
        comments = Comment.objects.aggregate(total=Count("id"), pending=Count("id", filter=Q(is_approved=False)))

        top = Post.objects.published().annotate(likes_total=Count("likes", distinct=True)).order_by("-views_count")[:5]
        top_posts = [{"title": p.title, "slug": p.slug, "views": p.views_count, "likes": p.likes_total} for p in top]

        recent = (Comment.objects.select_related("post").order_by("-created_at")
                  .values("id", "name", "content", "is_approved", "created_at", "post__title", "post__slug")[:5])
        recent_comments = [
            {"id": c["id"], "name": c["name"], "content": c["content"], "is_approved": c["is_approved"],
             "created_at": c["created_at"], "post_title": c["post__title"], "post_slug": c["post__slug"]}
            for c in recent
        ]

        today = timezone.localdate()
        months, y, m = [], today.year, today.month
        for _ in range(6):
            months.append((y, m))
            m -= 1
            if m == 0:
                m, y = 12, y - 1
        months.reverse()
        start = timezone.make_aware(datetime(months[0][0], months[0][1], 1))
        rows = (Post.objects.published().filter(published_at__gte=start)
                .annotate(month=TruncMonth("published_at")).values("month")
                .annotate(count=Count("id")).order_by("month"))
        counts = {(r["month"].year, r["month"].month): r["count"] for r in rows}

        return Response({
            "total_posts": posts["total"],
            "published_posts": posts["published"],
            "draft_posts": posts["draft"],
            "total_projects": Project.objects.count(),
            "total_skills": Skill.objects.count(),
            "total_comments": comments["total"],
            "pending_comments": comments["pending"],
            "total_likes": PostLike.objects.count(),
            "total_views": posts["views"] or 0,
            "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
            "top_posts": top_posts,
            "recent_comments": recent_comments,
            "posts_per_month": [{"month": f"{y}-{m:02d}", "count": counts.get((y, m), 0)} for y, m in months],
        })