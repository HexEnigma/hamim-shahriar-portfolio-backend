from django_filters import rest_framework as filters
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.pagination import MessagePagination, ProjectPagination
from core.permissions import IsOwner
from core.throttles import ContactThrottle

from .models import ContactMessage, Education, Experience, Profile, Project, Skill
from .serializers import (ContactCreateSerializer, ContactMessageSerializer, EducationSerializer,
                          ExperienceSerializer, ProfileSerializer, ProjectSerializer, SkillSerializer)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return Profile.get_solo()


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    pagination_class = None
    filterset_fields = ["category", "is_featured"]
    search_fields = ["name"]
    ordering_fields = ["display_order", "proficiency", "name"]


class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    pagination_class = None


class EducationViewSet(viewsets.ModelViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    pagination_class = None


class ProjectFilter(filters.FilterSet):
    tech = filters.CharFilter(method="filter_tech")

    class Meta:
        model = Project
        fields = ["category", "is_featured", "status"]

    def filter_tech(self, queryset, name, value):
        if value.isdigit():
            return queryset.filter(tech_stack__id=int(value))
        return queryset.filter(tech_stack__name__iexact=value)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.prefetch_related("tech_stack")
    serializer_class = ProjectSerializer
    lookup_field = "slug"
    lookup_value_regex = r"[-\w]+"
    pagination_class = ProjectPagination
    filterset_class = ProjectFilter
    search_fields = ["title", "summary", "description"]
    ordering_fields = ["completed_date", "display_order", "title"]


class ContactViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = ContactMessage.objects.all()
    pagination_class = MessagePagination
    filterset_fields = ["is_read"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        return [AllowAny()] if self.action == "create" else [IsOwner()]

    def get_throttles(self):
        return [ContactThrottle()] if self.action == "create" else super().get_throttles()

    def get_serializer_class(self):
        return ContactCreateSerializer if self.action == "create" else ContactMessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Thanks! Your message has been sent."}, status=201)