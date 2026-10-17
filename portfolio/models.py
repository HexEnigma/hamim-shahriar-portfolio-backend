from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from core.utils import unique_slug
from core.validators import validate_image, validate_resume

from .rules import experience_errors, project_errors


class Profile(TimeStampedModel):
    full_name = models.CharField(max_length=120)
    headline = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    location = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to="profile/", blank=True, null=True, validators=[validate_image])
    resume = models.FileField(upload_to="resume/", blank=True, null=True, validators=[validate_resume])
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    x_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    is_available_for_hire = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if self._state.adding and Profile.objects.exists():
            raise ValidationError("Only one Profile record is allowed. Edit the existing one.")
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj is None:   # editable placeholder; replace via dashboard
            obj = cls.objects.create(
                full_name="Hamim Shahriar",
                headline="Full Stack Developer | Python & Django | React | REST APIs",
            )
        return obj


class Skill(TimeStampedModel):
    class Category(models.TextChoices):
        FRONTEND = "FRONTEND", "Frontend"
        BACKEND = "BACKEND", "Backend"
        DATABASE = "DATABASE", "Database"
        DEVOPS = "DEVOPS", "DevOps"
        TOOLS = "TOOLS", "Tools"
        SOFT_SKILL = "SOFT_SKILL", "Soft skill"

    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    proficiency = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    icon = models.CharField(max_length=50, blank=True)   # icon key, e.g. "python"
    display_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Experience(TimeStampedModel):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full time"
        PART_TIME = "PART_TIME", "Part time"
        INTERNSHIP = "INTERNSHIP", "Internship"
        FREELANCE = "FREELANCE", "Freelance"
        CONTRACT = "CONTRACT", "Contract"

    company = models.CharField(max_length=160)
    role = models.CharField(max_length=160)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    location = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)     # one bullet per line
    company_url = models.URLField(blank=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["-start_date"]

    def clean(self):
        errors = experience_errors(self.start_date, self.end_date, self.is_current)
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.role} @ {self.company}"


class Education(TimeStampedModel):
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=60, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_year"]
        verbose_name_plural = "education"

    def __str__(self):
        return f"{self.degree}, {self.institution}"


class Project(TimeStampedModel):
    class Category(models.TextChoices):
        WEB = "WEB", "Web"
        MOBILE = "MOBILE", "Mobile"
        API = "API", "API"
        ML = "ML", "Machine learning"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.CharField(max_length=200)
    description = models.TextField()
    cover_image = models.ImageField(upload_to="projects/", blank=True, null=True, validators=[validate_image])
    tech_stack = models.ManyToManyField(Skill, blank=True, related_name="projects")
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.WEB)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.COMPLETED)
    live_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-completed_date"]

    def clean(self):
        errors = project_errors(self.live_url, self.github_url)
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Project, self.title, "project")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.subject}"