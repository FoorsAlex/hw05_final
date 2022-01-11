import http
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import ImageFieldFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create(username='author')
        cls.authorized_user = Client()
        cls.guest_user = Client()
        cls.authorized_user.force_login(cls.user_auth)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_auth,
            group=cls.group,
            image=cls.uploaded
        )
        cls.reverse_login = reverse('users:login')
        cls.reverse_create = reverse('posts:post_create')
        cls.reverse_add_comment = reverse(
            'posts:add_comment', kwargs={'post_id': cls.post.pk}
        )

    def test_create_authorized_user(self):
        """Валидная форма создает запись в Post."""

        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст1',
            'author': self.user_auth,
            'group': self.group.id,
            'image': self.post.image
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'author'}
        ))
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=form_data['author'],
                group=form_data['group'],
            ).exists()
        )
        fields = {
            'text': Post.objects.get(author=self.user_auth, id=2).text,
            'author': self.post.author,
            'group': self.post.group.id,
        }
        for field, expected_field in fields.items():
            with self.subTest(field=field):
                self.assertEqual(form_data[field], expected_field)
        self.assertIsInstance(self.post.image, ImageFieldFile)

    def test_edit(self):
        """Валидная форма редактирует запись в Post."""

        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'author': self.user_auth,
            'group': self.group.id,
            'image': self.uploaded.name
        }
        response = self.authorized_user.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=form_data['author'],
                group=form_data['group'],
                image=self.post.image
            ).exists()
        )

    def test_create_guest_user(self):
        """Проверяет может-ли гость создавать посты
        Зочем? Пусть будет."""

        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст гостя',
        }
        response = self.guest_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        reverse_url = (self.reverse_login + '?next=' + self.reverse_create)
        self.assertRedirects(response, reverse_url)
        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_create_comment_guest_user(self):
        """Проверяет может-ли гость комментировать
        Зочем? Пусть будет."""

        tasks_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент гостя',
        }
        response = self.guest_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        login = self.reverse_login
        add_comment = self.reverse_add_comment
        reverse_url = (login + '?next=' + add_comment)
        self.assertRedirects(response, reverse_url)
        self.assertEqual(Comment.objects.count(), tasks_count)
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_create_comment_auth_user(self):
        """Проверяет может-ли гость комментировать
        Зочем? Пусть будет."""

        tasks_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), tasks_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )
