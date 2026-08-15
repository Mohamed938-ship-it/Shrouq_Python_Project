from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post, Comment


class HomePageTests(TestCase):
    def test_homepage_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")


class PostDetailTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="alice", password="testpass123")
        self.post = Post.objects.create(
            title="First post", body="Hello there", author=self.author
        )

    def test_post_detail_loads(self):
        response = self.client.get(reverse("post_detail", args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First post")


class CreatePostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="testpass123")

    def test_anonymous_user_cannot_create_post(self):
        response = self.client.post(
            reverse("add_post"), {"title": "Sneaky post", "body": "..."}
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(title="Sneaky post").exists())

    def test_logged_in_user_can_create_post(self):
        self.client.login(username="bob", password="testpass123")
        response = self.client.post(
            reverse("add_post"), {"title": "My new post", "body": "Some content"}
        )
        post = Post.objects.get(title="My new post")
        self.assertRedirects(response, post.get_absolute_url())
        self.assertEqual(post.author, self.user)


class CommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carol", password="testpass123")
        self.author = User.objects.create_user(username="dave", password="testpass123")
        self.post = Post.objects.create(
            title="A post", body="Content", author=self.author
        )

    def test_user_can_comment(self):
        self.client.login(username="carol", password="testpass123")
        response = self.client.post(
            reverse("post_detail", args=[self.post.pk]), {"body": "Nice post!"}
        )
        self.assertRedirects(response, reverse("post_detail", args=[self.post.pk]))
        self.assertTrue(
            Comment.objects.filter(post=self.post, author=self.user, body="Nice post!").exists()
        )


class RegistrationTests(TestCase):
    def test_registration_stores_hashed_password(self):
        self.client.post(
            reverse("register"),
            {"username": "erin", "email": "erin@example.com", "password": "testpass123"},
        )
        user = User.objects.get(username="erin")
        self.assertNotEqual(user.password, "testpass123")
        self.assertTrue(user.check_password("testpass123"))


class EditDeletePostTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="frank", password="testpass123")
        self.other = User.objects.create_user(username="grace", password="testpass123")
        self.post = Post.objects.create(
            title="Owned post", body="Original body", author=self.owner
        )

    def test_owner_can_edit_post(self):
        self.client.login(username="frank", password="testpass123")
        response = self.client.post(
            reverse("edit_post", args=[self.post.pk]),
            {"title": "Updated title", "body": "Updated body"},
        )
        self.post.refresh_from_db()
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(self.post.title, "Updated title")

    def test_other_user_cannot_edit_post(self):
        self.client.login(username="grace", password="testpass123")
        self.client.post(
            reverse("edit_post", args=[self.post.pk]),
            {"title": "Hijacked title", "body": "Hijacked body"},
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Owned post")

    def test_owner_can_delete_post(self):
        self.client.login(username="frank", password="testpass123")
        response = self.client.post(reverse("delete_post", args=[self.post.pk]))
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_other_user_cannot_delete_post(self):
        self.client.login(username="grace", password="testpass123")
        self.client.post(reverse("delete_post", args=[self.post.pk]))
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
