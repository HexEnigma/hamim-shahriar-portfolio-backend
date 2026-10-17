from django.utils import timezone


def experience_errors(start, end, current):
    errors = {}
    if start and start > timezone.localdate():
        errors["start_date"] = "Start date cannot be in the future."
    if current:
        if end:
            errors["end_date"] = "End date must be empty for a current role."
    elif not end:
        errors["end_date"] = "End date is required unless this is your current role."
    elif start and end <= start:
        errors["end_date"] = "End date must be after start date."
    return errors


def project_errors(live_url, github_url):
    if live_url or github_url:
        return {}
    msg = "Provide at least one of live URL or GitHub URL."
    return {"live_url": msg, "github_url": msg}