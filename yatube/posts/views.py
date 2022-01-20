from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def get_paginator_obj(request, query_list):
    paginator = Paginator(query_list, settings.COUNT_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    templates = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = get_paginator_obj(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, templates, context)


def group_posts(request, slug):
    templates = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.group_posts.all()
    page_obj = get_paginator_obj(request, posts_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, templates, context)


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    following = (user.is_authenticated
                 and Follow.objects.filter(user=user, author=author).exists())
    post_list = Post.objects.filter(author__username=username)
    count_posts = post_list.count()
    page_obj = get_paginator_obj(request, post_list)
    client = get_object_or_404(User, username=username)
    context = {
        'client': client,
        'count_posts': count_posts,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_list = Post.objects.filter(author__username=post.author)
    count_posts = post_list.count()
    comment_form = CommentForm()
    comment_list = post.comments.all()
    context = {
        'post': post,
        'count_posts': count_posts,
        'comment_form': comment_form,
        'comments': comment_list
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    client = request.user
    form = PostForm(
        request.POST or None,
        files=request.FILES or None, )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = client
        post.save()
        return redirect('posts:profile', username=post.author.username)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    client = request.user
    post = get_object_or_404(Post, id=post_id)
    if post.author != client:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'template': template
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    page_obj = get_paginator_obj(request, post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        follower = get_object_or_404(Follow, user=request.user, author=author)
        follower.delete()
    return redirect('posts:profile', username=username)
