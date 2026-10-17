from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from blog.models import Category, Comment, Post
from portfolio.models import Profile

User = get_user_model()
PW = "Str0ng-pass-123"
LONG = "word " * 120


class Base(APITestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_superuser("owner", "owner@example.com", PW)
        self.normal = User.objects.create_user("normal", "normal@example.com", PW)
        self.cat = Category.objects.create(name="Django")
        self.pub = Post.objects.create(title="Published post", excerpt="x", content=LONG,
                                       category=self.cat, author=self.owner, status="PUBLISHED")
        self.draft = Post.objects.create(title="Secret draft", excerpt="x", content=LONG,
                                         category=self.cat, author=self.owner)

    def login_as(self, username):
        r = self.client.post("/api/auth/login/", {"username": username, "password": PW}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        return r.data


class AuthAndPermissionTests(Base):
    def test_visitor_cannot_write(self):
        self.assertEqual(self.client.post("/api/posts/", {"title": "hack"}, format="json").status_code, 401)

    def test_normal_user_cannot_write(self):
        self.login_as("normal")
        self.assertEqual(self.client.post("/api/skills/", {}, format="json").status_code, 403)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

    def test_register_does_not_exist(self):
        with self.assertRaises(Resolver404):
            resolve('/api/auth/register/')

    def test_login_failure_is_generic(self):
        a = self.client.post("/api/auth/login/", {"username": "owner", "password": "bad"}, format="json")
        b = self.client.post("/api/auth/login/", {"username": "ghost", "password": "bad"}, format="json")
        self.assertEqual((a.status_code, b.status_code), (401, 401))
        self.assertEqual(a.json()["detail"], b.json()["detail"])

    def test_me_and_logout_blacklist(self):
        data = self.login_as("owner")
        self.assertEqual(self.client.get("/api/auth/me/").json()["username"], "owner")
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": data["refresh"]}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": data["refresh"]}, format="json").status_code, 401)

    def test_dashboard_owner_only(self):
        self.assertEqual(self.client.get("/api/dashboard/stats/").status_code, 401)
        self.login_as("owner")
        r = self.client.get("/api/dashboard/stats/")
        self.assertEqual(r.status_code, 200)
        for key in ("total_posts", "published_posts", "draft_posts", "total_projects", "total_skills",
                    "total_comments", "pending_comments", "total_likes", "total_views", "unread_messages",
                    "top_posts", "recent_comments", "posts_per_month"):
            self.assertIn(key, r.json())
        self.assertEqual(len(r.json()["posts_per_month"]), 6)


class PrivacyTests(Base):
    def test_draft_hidden_from_visitors(self):
        self.assertEqual(self.client.get("/api/posts/secret-draft/").status_code, 404)
        self.assertNotIn("Secret draft", self.client.get("/api/posts/").content.decode())

    def test_owner_can_see_drafts(self):
        self.login_as("owner")
        self.assertEqual(self.client.get("/api/posts/secret-draft/").status_code, 200)
        self.assertIn("Secret draft", self.client.get("/api/posts/?status=DRAFT").content.decode())

    def test_unapproved_comments_and_emails_hidden(self):
        Comment.objects.create(post=self.pub, name="Pat", email="pat@secret.com", content="Visible comment", is_approved=True)
        Comment.objects.create(post=self.pub, name="Sam", email="sam@secret.com", content="Hidden comment")
        body = self.client.get(f"/api/posts/{self.pub.slug}/comments/").content.decode()
        self.assertIn("Visible comment", body)
        self.assertNotIn("Hidden comment", body)
        self.assertNotIn("secret.com", body)
        self.assertEqual(self.client.get("/api/comments/").status_code, 401)

    def test_contact_inbox_private(self):
        self.assertEqual(self.client.get("/api/contact/").status_code, 401)


class InteractionTests(Base):
    def test_like_toggle(self):
        url = f"/api/posts/{self.pub.slug}/like/"
        self.assertEqual(self.client.post(url, HTTP_X_VISITOR_ID="abc").json(), {"liked": True, "likes_count": 1})
        self.assertEqual(self.client.post(url, HTTP_X_VISITOR_ID="abc").json(), {"liked": False, "likes_count": 0})

    def test_like_requires_visitor_header(self):
        self.assertEqual(self.client.post(f"/api/posts/{self.pub.slug}/like/").status_code, 400)

    def test_view_counter_cooldown(self):
        url = f"/api/posts/{self.pub.slug}/"
        self.client.get(url, HTTP_X_VISITOR_ID="v1")
        self.client.get(url, HTTP_X_VISITOR_ID="v1")
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.views_count, 1)
        self.client.get(url, HTTP_X_VISITOR_ID="v2")
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.views_count, 2)

    def test_comment_awaits_approval(self):
        url = f"/api/posts/{self.pub.slug}/comments/"
        r = self.client.post(url, {"name": "Pat", "email": "pat@example.com", "content": "Nice article!"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("awaiting approval", r.json()["detail"])
        self.assertEqual(self.client.get(url).json()["count"], 0)

    def test_comment_validation(self):
        r = self.client.post(f"/api/posts/{self.pub.slug}/comments/",
                             {"name": "P", "email": "bad", "content": "no"}, format="json")
        self.assertEqual(r.status_code, 400)
        for field in ("name", "email", "content"):
            self.assertIn(field, r.json())

    def test_owner_approval_makes_comment_public(self):
        c = Comment.objects.create(post=self.pub, name="Pat", email="p@x.com", content="Approve me please")
        self.login_as("owner")
        self.assertEqual(self.client.patch(f"/api/comments/{c.pk}/", {"is_approved": True}, format="json").status_code, 200)
        self.client.credentials()
        self.assertIn("Approve me please", self.client.get(f"/api/posts/{self.pub.slug}/comments/").content.decode())

    def test_comment_throttle(self):
        url = f"/api/posts/{self.pub.slug}/comments/"
        payload = {"name": "Pat", "email": "pat@example.com", "content": "Hello there"}
        codes = [self.client.post(url, payload, format="json").status_code for _ in range(6)]
        self.assertEqual(codes, [201] * 5 + [429])

    def test_contact_flow_and_throttle(self):
        payload = {"name": "Ann", "email": "ann@example.com", "subject": "Hello", "message": "I would like to talk."}
        codes = [self.client.post("/api/contact/", payload, format="json").status_code for _ in range(4)]
        self.assertEqual(codes, [201, 201, 201, 429])
        short = self.client.post("/api/contact/", {**payload, "message": "short"}, format="json")
        self.assertIn(short.status_code, (400, 429))


class ValidationTests(Base):
    def post_payload(self, **over):
        return {"title": "A solid title", "excerpt": "short", "content": LONG,
                "category": self.cat.pk, "status": "DRAFT", **over}

    def test_post_rules(self):
        self.login_as("owner")
        self.assertEqual(self.client.post("/api/posts/", self.post_payload(title="abc"), format="json").status_code, 400)
        r = self.client.post("/api/posts/", self.post_payload(status="PUBLISHED", content="short"), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("content", r.json())
        r = self.client.post("/api/posts/", self.post_payload(status="PUBLISHED", category=None), format="json")
        self.assertIn("category", r.json())

    def test_published_at_set_once(self):
        self.login_as("owner")
        slug = self.client.post("/api/posts/", self.post_payload(), format="json").json()["slug"]
        url = f"/api/posts/{slug}/"
        first = self.client.patch(url, {"status": "PUBLISHED"}, format="json").json()["published_at"]
        self.assertIsNotNone(first)
        self.client.patch(url, {"status": "DRAFT"}, format="json")
        again = self.client.patch(url, {"status": "PUBLISHED"}, format="json").json()["published_at"]
        self.assertEqual(first, again)

    def test_reading_time_computed(self):
        self.assertEqual(self.pub.reading_time, 1)

    def test_skill_proficiency_range(self):
        self.login_as("owner")
        base = {"name": "Python", "category": "BACKEND"}
        self.assertEqual(self.client.post("/api/skills/", {**base, "proficiency": 0}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/skills/", {**base, "proficiency": 101}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/skills/", {**base, "proficiency": 80}, format="json").status_code, 201)

    def test_experience_rules(self):
        self.login_as("owner")
        base = {"company": "X", "role": "Dev", "employment_type": "INTERNSHIP", "start_date": "2024-01-01"}
        bad = [{**base, "is_current": False},
               {**base, "is_current": True, "end_date": "2024-06-01"},
               {**base, "is_current": False, "end_date": "2023-01-01"},
               {**base, "start_date": "2999-01-01", "is_current": True}]
        for payload in bad:
            self.assertEqual(self.client.post("/api/experiences/", payload, format="json").status_code, 400, payload)
        self.assertEqual(self.client.post("/api/experiences/", {**base, "is_current": True}, format="json").status_code, 201)

    def test_project_needs_a_link(self):
        self.login_as("owner")
        base = {"title": "Proj", "summary": "s", "description": "d", "category": "WEB"}
        r = self.client.post("/api/projects/", base, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("github_url", r.json())
        r = self.client.post("/api/projects/", {**base, "github_url": "https://github.com/HexEnigma/x"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["slug"], "proj")

    def test_category_in_use_cannot_be_deleted(self):
        self.login_as("owner")
        r = self.client.delete(f"/api/categories/{self.cat.pk}/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("detail", r.json())


class ProfileAndUploadTests(Base):
    def test_profile_singleton(self):
        Profile.get_solo()
        with self.assertRaises(ValidationError):
            Profile(full_name="x", headline="y").save()

    def test_profile_public_read_visitor_cannot_write(self):
        self.assertEqual(self.client.get("/api/profile/").status_code, 200)
        self.assertEqual(self.client.patch("/api/profile/", {"headline": "x"}, format="json").status_code, 401)

    def test_bad_avatar_rejected(self):
        self.login_as("owner")
        bad = SimpleUploadedFile("evil.txt", b"not an image", content_type="text/plain")
        self.assertEqual(self.client.patch("/api/profile/", {"avatar": bad}, format="multipart").status_code, 400)

    def test_resume_must_be_pdf(self):
        self.login_as("owner")
        fake = SimpleUploadedFile("cv.pdf", b"not really a pdf", content_type="application/pdf")
        self.assertEqual(self.client.patch("/api/profile/", {"resume": fake}, format="multipart").status_code, 400)