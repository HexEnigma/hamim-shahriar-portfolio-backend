from rest_framework import serializers

from core.serializers import ResolveMixin

from .models import ContactMessage, Education, Experience, Profile, Project, Skill
from .rules import experience_errors, project_errors


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "full_name", "headline", "bio", "email", "phone", "location", "avatar", "resume",
                  "github_url", "linkedin_url", "x_url", "website_url", "years_of_experience",
                  "is_available_for_hire", "updated_at"]


class SkillSerializer(serializers.ModelSerializer):
    proficiency = serializers.IntegerField(
        min_value=1, max_value=100,
        error_messages={"min_value": "Proficiency must be between 1 and 100.",
                        "max_value": "Proficiency must be between 1 and 100.",
                        "invalid": "Proficiency must be a whole number."},
    )

    class Meta:
        model = Skill
        fields = ["id", "name", "category", "proficiency", "icon", "display_order", "is_featured"]


class ExperienceSerializer(ResolveMixin, serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ["id", "company", "role", "employment_type", "location", "start_date", "end_date",
                  "is_current", "description", "company_url", "display_order"]

    def validate(self, attrs):
        errors = experience_errors(self.resolve(attrs, "start_date"), self.resolve(attrs, "end_date"),
                                   self.resolve(attrs, "is_current", False))
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class EducationSerializer(ResolveMixin, serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ["id", "institution", "degree", "field_of_study", "start_year", "end_year", "grade", "description"]

    def validate(self, attrs):
        start, end = self.resolve(attrs, "start_year"), self.resolve(attrs, "end_year")
        if start and end and end < start:
            raise serializers.ValidationError({"end_year": "End year cannot be before start year."})
        return attrs


class ProjectSerializer(ResolveMixin, serializers.ModelSerializer):
    tech_stack = SkillSerializer(many=True, read_only=True)
    tech_stack_ids = serializers.PrimaryKeyRelatedField(
        source="tech_stack", queryset=Skill.objects.all(), many=True, write_only=True, required=False)

    class Meta:
        model = Project
        fields = ["id", "title", "slug", "summary", "description", "cover_image", "tech_stack", "tech_stack_ids",
                  "category", "status", "live_url", "github_url", "is_featured", "completed_date",
                  "display_order", "created_at", "updated_at"]
        read_only_fields = ["slug"]

    def validate(self, attrs):
        errors = project_errors(self.resolve(attrs, "live_url"), self.resolve(attrs, "github_url"))
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ContactMessageSerializer(serializers.ModelSerializer):   # owner inbox
    class Meta:
        model = ContactMessage
        fields = ["id", "name", "email", "subject", "message", "is_read", "created_at"]
        read_only_fields = ["name", "email", "subject", "message", "created_at"]


class ContactCreateSerializer(serializers.ModelSerializer):    # public
    name = serializers.CharField(min_length=2, max_length=120,
                                 error_messages={"min_length": "Name must be at least 2 characters."})
    subject = serializers.CharField(min_length=3, max_length=200,
                                    error_messages={"min_length": "Subject must be at least 3 characters."})
    message = serializers.CharField(min_length=10, max_length=2000,
                                    error_messages={"min_length": "Message must be at least 10 characters.",
                                                    "max_length": "Message must be 2000 characters or fewer."})

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]