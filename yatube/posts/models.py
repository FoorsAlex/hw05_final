from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок',
        help_text='Укажите название группы'
    )
    slug = models.SlugField(unique=True)
    description = models.TextField(
        verbose_name='Описание',
        help_text='Опишите о чём ваше сообщество'
    )

    def __str__(self):
        return str(self.title)


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Напишите о чём хотели-бы рассказать'
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Выберите автора'
    )
    group = models.ForeignKey(
        Group,
        related_name='group_posts',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Выберите группу'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Коментарий',
        help_text='Напишите свой комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
        help_text='Выберите автора'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Прокомментируйте пост'
    )
    created = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор на которого пользователь подписался'
    )

    class Meta:
        UniqueConstraint(fields=['user', 'author'],
                         name='unique_booking')
