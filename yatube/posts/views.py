from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from core.constants.constants import (get_object_or_none,
                                      ELEMENTS_PER_PAGE,
                                      CACHE_SECONDS)
from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def paginator(request, list):
    paginator = Paginator(list, ELEMENTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(CACHE_SECONDS, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related().all()
    page_obj = paginator(request, post_list)
    template = "posts/index.html"
    title = "Последние обновления на сайте"
    title_body = "Последние обновления на сайте"
    context = {
        "page_obj": page_obj,
        "title": title,
        "title_body": title_body,
    }
    return render(request, template, context)


def group_post(request, slug):
    group = get_object_or_404(Group, slug=slug)
    description_body = group.description
    group_list = Post.objects.select_related('group').filter(group=group)
    page_obj = paginator(request, group_list)
    template = "posts/group_list.html"
    title = group.title
    title_body = group.title
    context = {
        "title": title,
        "description_body": description_body,
        "title_body": title_body,
        'slug': slug,
        'page_obj': page_obj,

    }
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.select_related('author').filter(author=user)
    page_obj = paginator(request, posts)
    following = False
    if request.user.is_authenticated:
        is_follow = get_object_or_none(Follow, user=request.user, author=user)
        if is_follow:
            following = True

    if request.user == user:
        not_self_follow = False
    else:
        not_self_follow = True

    context = {
        'username': user,
        'page_obj': page_obj,
        'following': following,
        'not_self_follow': not_self_follow,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    username = post.author
    thirty_symbols = post.text[:30]
    form_comment = CommentForm()
    post_comments = Comment.objects.select_related('post').filter(post=post_id)
    context = {
        'post': post,
        'thirty_symbols': thirty_symbols,
        'post_id': post_id,
        'form_comment': form_comment,
        'post_comments': post_comments,
        'username': username,

    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(request.POST,
                        files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:profile", post.author)
    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:
        if request.method == 'POST':
            form = PostForm(request.POST,
                            files=request.FILES or None,
                            instance=post)
            if form.is_valid():
                form.save()
                return redirect("posts:post_detail", post_id)
        form = PostForm(instance=post)
        return render(request, template, {'form': form, 'is_edit': True,
                                          'post_id': post_id})


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
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

    posts_list = Post.objects.select_related('author').filter(
        author__following__user=user)
    page_obj = paginator(request, posts_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect('posts:main')


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.get(
        user=User.objects.get(username=user),
        author=User.objects.get(username=username),
    ).delete()
    return redirect('posts:main')
