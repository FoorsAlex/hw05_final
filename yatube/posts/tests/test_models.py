from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа'
        )

    def test_models_have_correct_object_names(self):
        """Проверка работы __str__"""

        post = PostModelTest.post
        group = PostModelTest.group
        objects_names = {
            'post': [post, post.text[:15]],
            'group': [group, group.title]
        }
        for objects, name in objects_names.items():
            with self.subTest(objects=objects):
                self.assertEqual(str(name[0]), name[1])

    def test_labels_verbose_name(self):
        """verbose_name полей совпадает с ожидаемым."""

        post = PostModelTest.post
        group = PostModelTest.group
        objects_labels = {
            'post_text': [post, 'text', 'Текст'],
            'post_author': [post, 'author', 'Автор'],
            'post_group': [post, 'group', 'Группа'],
            'group_title': [group, 'title', 'Заголовок'],
            'group_description': [group, 'description', 'Описание']
        }
        for label, verbose_name in objects_labels.items():
            with self.subTest(label=label):
                verbose = verbose_name[0]._meta.get_field(
                    verbose_name[1]).verbose_name
                self.assertEqual(verbose, verbose_name[2])

    def test_labels_help_text(self):
        """help_text полей совпадает с ожидаемым."""

        post = PostModelTest.post
        group = PostModelTest.group
        objects_labels = {
            'post_text': [post,
                          'text',
                          'Напишите о чём хотели-бы рассказать'
                          ],
            'post_author': [post,
                            'author',
                            'Выберите автора'
                            ],
            'post_group': [post,
                           'group',
                           'Выберите группу'
                           ],
            'group_title': [group,
                            'title',
                            'Укажите название группы'
                            ],
            'group_description': [
                group,
                'description',
                'Опишите о чём ваше сообщество'
            ]
        }
        for label, help_text in objects_labels.items():
            with self.subTest(label=label):
                verbose = help_text[0]._meta.get_field(help_text[1]).help_text
                self.assertEqual(verbose, help_text[2])
