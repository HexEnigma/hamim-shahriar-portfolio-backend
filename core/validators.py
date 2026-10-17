import os

from django.core.exceptions import ValidationError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_RESUME_BYTES = 5 * 1024 * 1024


def validate_image(file):
    if getattr(file, "_committed", False):   # already-stored file
        return
    if os.path.splitext(file.name)[1].lower() not in IMAGE_EXTENSIONS:
        raise ValidationError("Only .jpg, .jpeg, .png and .webp images are allowed.")
    if file.size > MAX_IMAGE_BYTES:
        raise ValidationError("Image must be 2 MB or smaller.")


def validate_resume(file):
    if getattr(file, "_committed", False):
        return
    if os.path.splitext(file.name)[1].lower() != ".pdf":
        raise ValidationError("Resume must be a PDF file.")
    if file.size > MAX_RESUME_BYTES:
        raise ValidationError("Resume must be 5 MB or smaller.")
    file.seek(0)
    head = file.read(5)
    file.seek(0)
    if head != b"%PDF-":
        raise ValidationError("This file is not a valid PDF.")