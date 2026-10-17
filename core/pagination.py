from rest_framework.pagination import PageNumberPagination


class PostPagination(PageNumberPagination):
    page_size = 6

class ProjectPagination(PageNumberPagination):
    page_size = 9

class CommentPagination(PageNumberPagination):
    page_size = 10

class MessagePagination(PageNumberPagination):
    page_size = 10