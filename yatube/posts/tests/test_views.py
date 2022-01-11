import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPages(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create(username='author')
        cls.user = User.objects.create(username='user_follow')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug',
            description='Описание'
        )
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
        cls.post = Post.objects.create(
            text='Текст',
            group=cls.group,
            author=cls.user_auth,
            image=cls.uploaded,
        )
        Comment.objects.create(
            text='Комментарий',
            author=cls.user_auth,
            post=cls.post
        )
        Follow.objects.create(
            author=cls.user_auth,
            user=cls.user
        )
        cls.comments = Comment.objects.filter(post__id=cls.post.pk)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client_authorized = Client()
        self.client_authorized_user = Client()
        self.client_authorized.force_login(self.user_auth)
        self.client_authorized_user.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': self.user_auth.username}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ),
            'posts/create_post.html': reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ),
            'posts/follow.html': reverse('posts:follow_index')
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client_authorized.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.client_authorized.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_pages_with_paginator_show_correct_context(self):
        """Шаблоны страниц с паджинатором сформированы
         с правильным контекстом."""

        pages_kwargs = {
            'posts:group_list': ('slug', self.group.slug),
            'posts:profile': ('username', self.user_auth.username),
            'posts:index': (),
            'posts:follow_index': ()
        }
        for reverse_name, kwargs in pages_kwargs.items():
            with self.subTest(reverse_name=reverse_name):
                if reverse_name == 'posts:index' or reverse_name == 'posts:follow_index':
                    response = self.client_authorized_user.get(
                        reverse(reverse_name))
                else:
                    response = self.client_authorized_user.get(
                        reverse(reverse_name,
                                kwargs={kwargs[0]: kwargs[1]}))
                first_object = response.context['page_obj'][0]
                task_text_0 = first_object.text
                task_group_0 = first_object.group
                task_author_0 = first_object.author
                task_image_0 = first_object.image
                self.assertEqual(task_text_0, self.post.text)
                self.assertEqual(task_group_0, self.group)
                self.assertEqual(task_author_0, self.user_auth)
                self.assertEqual(task_image_0, self.post.image)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""

        response = self.client_authorized.get(reverse('posts:post_create', ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = self.client_authorized.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = (self.client_authorized.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.group)
        self.assertEqual(response.context.get('post').author, self.user_auth)
        self.assertCountEqual(response.context.get('comments'), self.comments)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create(username='author')
        cls.user = User.objects.create(username='follow_user')
        Follow.objects.create(
            author=cls.user_auth,
            user=cls.user
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug',
            description='Описание'
        )
        count_post_obj = 13
        object_post = [
            Post(
                text=f'Текст {i}',
                author=cls.user_auth,
                group=cls.group
            )
            for i in range(0, count_post_obj)
        ]
        Post.objects.bulk_create(object_post)

    def setUp(self):
        self.client_authorized = Client()
        self.client_authorized.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка работы паджинатора 1-я страница"""

        count_pages = 10
        reverse_list = {
            'posts:group_list': ('slug', self.group.slug),
            'posts:profile': ('username', self.user_auth.username),
            'posts:index': (),
            'posts:follow_index': ()
        }
        for reverse_url, kwargs in reverse_list.items():
            with self.subTest(reverse_url=reverse_url):
                if reverse_url == 'posts:profile' or reverse_url == 'posts:group_list':
                    response = self.client_authorized.get(
                        reverse(reverse_url, kwargs={kwargs[0]: kwargs[1]})
                    )
                else:
                    response = self.client_authorized.get(
                        reverse(reverse_url)
                    )
                self.assertEqual(
                    len(response.context['page_obj']), count_pages, reverse_url)

    def test_second_page_contains_three_records(self):
        """Проверка работы паджинатора 2-я страница"""

        count_pages = 3
        reverse_list = {
            'posts:group_list': ('slug', self.group.slug),
            'posts:profile': ('username', self.user_auth.username),
            'posts:index': (),
            'posts:follow_index': ()
        }
        for reverse_url, kwargs in reverse_list.items():
            with self.subTest(reverse_url=reverse_url):
                if reverse_url == 'posts:profile' or reverse_url == 'posts:group_list':
                    response = self.client_authorized.get(
                        reverse(reverse_url, kwargs={kwargs[0]: kwargs[1]}) + '?page=2'
                    )
                else:
                    response = self.client_authorized.get(
                        reverse(reverse_url) + '?page=2'
                    )
                self.assertEqual(
                    len(response.context['page_obj']), count_pages
                )


class TestCash(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create(username='author')
        cls.post = Post.objects.create(
            text='Тест кэша',
            author=cls.user_auth
        )
        cls.reverse_index = reverse('posts:index')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_auth)

    def test_cash_index_page(self):
        """Тестирует работу кэширования на
        главной странице"""

        response_1 = self.authorized_client.get(self.reverse_index)
        content_1 = response_1.content
        self.post.delete()
        response_2 = self.authorized_client.get(self.reverse_index)
        content_2 = response_2.content
        self.assertEqual(content_1, content_2)


class TestFollow(TestCase):

    def setUp(self):
        self.authorized_user = User.objects.create(username='user')
        self.authorized_user_author = User.objects.create(username='author')
        self.post = Post.objects.create(
            text='Текст',
            author=self.authorized_user_author
        )
        Follow.objects.create(
            user=self.authorized_user,
            author=self.authorized_user_author
        )
        self.authorized_client_auth = Client()
        self.authorized_client = Client()
        self.authorized_client_auth.force_login(self.authorized_user_author)
        self.authorized_client.force_login(self.authorized_user)

    def test_follow_index_auth(self):
        response = self.authorized_client_auth.get(reverse(
            'posts:follow_index'))
        post_obj = response.context['page_obj']
        self.assertFalse(post_obj)

    def test_follow_index_user(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_obj = response.context['page_obj'][0]
        self.assertTrue(post_obj)

    def test_unfollow(self):
        follow_count_1 = Follow.objects.count()
        follow = Follow.objects.get(
            user=self.authorized_user,
            author=self.authorized_user_author
        )
        follow.delete()
        follow_count_2 = Follow.objects.count()
        self.assertEqual(follow_count_2, follow_count_1 - 1)
