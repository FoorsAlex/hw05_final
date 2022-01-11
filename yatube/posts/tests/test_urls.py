import http

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index = '/'
        cls.about_tech = '/about/tech/'
        cls.about_author = '/about/author/'

    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get(self.index)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_about_tech(self):
        response = self.guest_client.get(self.about_tech)
        self.assertEqual(response.status_code, http.HTTPStatus.OK,
                         'Проблемки со страницой "О технологиях"')

    def test_about_author(self):
        response = self.guest_client.get(self.about_author)
        self.assertEqual(response.status_code, http.HTTPStatus.OK,
                         'Проблемки со страницой "Об авторе"')


class NotStaticUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create(username='author')
        cls.user = User.objects.create(username='user')
        cls.post = Post.objects.create(
            author=cls.auth_user,
            text='test_text',
        )
        cls.group = Group.objects.create(
            title='title',
            slug='test_slug',
            description='test_description'

        )
        cls.urls_all_access = {
            '/': http.HTTPStatus.OK,
            f'/group/{cls.group.slug}/': http.HTTPStatus.OK,
            f'/profile/{cls.auth_user.username}/': http.HTTPStatus.OK,
            f'/posts/{cls.post.id}/': http.HTTPStatus.OK,
            'unexisting_page/': http.HTTPStatus.NOT_FOUND,
            f'/posts/{cls.post.id}/edit/': http.HTTPStatus.FOUND,
            '/create/': http.HTTPStatus.FOUND,
            '/follow/': http.HTTPStatus.FOUND,
            f'/profile/{cls.auth_user.username}/follow/': http.HTTPStatus.FOUND,
            f'/profile/{cls.auth_user.username}/unfollow/': http.HTTPStatus.FOUND,
            f'/posts/{cls.post.id}/comment': http.HTTPStatus.FOUND

        }
        cls.templates_authorized = {
            '/create/': 'posts/create_post.html',
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.auth_user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',


        }
        cls.templates_guest = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.auth_user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_auth = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_auth.force_login(self.auth_user)

    def test_url_availability(self):
        """Проверка доступности страниц для
        неавторизированного пользователя и перенаправления
        на страницу авторизации"""

        for url, expected_value in self.urls_all_access.items():
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code, expected_value, url)

    def test_url_limit_availability(self):
        """Проверка доступа к редактированнию
         поста для автора и для просто
          авторизированного пользователя,
          а также доступа к странице создания"""

        response_authorized_edit = self.authorized_client.get('/posts/1/edit/')
        self.assertRedirects(response_authorized_edit, '/posts/1/',
                             status_code=http.HTTPStatus.FOUND,
                             target_status_code=http.HTTPStatus.OK)

    def test_template_all_access(self):
        """Проверка шаблонов для неавторизированного пользователя"""

        for url, template in self.templates_guest.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(self.guest_client.get(url), template)

    def test_template_limit_access(self):
        """Проверка шаблонов для
         авторизированного пользователя"""

        for url, template in self.templates_authorized.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized_client.get(url), template)
