from django.contrib import admin

from .models import ContactMessage, Education, Experience, Profile, Project, Skill


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "headline", "email", "is_available_for_hire")
    search_fields = ("full_name", "headline", "email")
    list_filter = ("is_available_for_hire",)

    def has_add_permission(self, request):
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "proficiency", "is_featured", "display_order")
    search_fields = ("name",)
    list_filter = ("category", "is_featured")


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("role", "company", "employment_type", "start_date", "end_date", "is_current")
    search_fields = ("role", "company")
    list_filter = ("employment_type", "is_current")


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("degree", "institution", "start_year", "end_year")
    search_fields = ("degree", "institution", "field_of_study")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "is_featured", "completed_date")
    search_fields = ("title", "summary")
    list_filter = ("category", "status", "is_featured")
    readonly_fields = ("slug",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    list_filter = ("is_read",)