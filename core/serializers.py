class ResolveMixin:
    """Value from incoming data, else the existing instance (for PATCH)."""
    def resolve(self, attrs, key, default=None):
        if key in attrs:
            return attrs[key]
        if self.instance is not None:
            return getattr(self.instance, key, default)
        return default