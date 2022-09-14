from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post


User = get_user_model()


def paginator(request, list):
    paginator = Paginator(list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
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
    group_list = Post.objects.filter(group=group).order_by('-pub_date')
    page_obj = paginator(request, group_list)
    template = "posts/group_list.html"
    title = 'Лев Толстой – зеркало русской революции.'
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
    posts = Post.objects.filter(author=user).order_by('-pub_date')
    posts_count = posts.count()
    page_obj = paginator(request, posts)
    following = False
    try:
        if Follow.objects.filter(user=request.user, author=user).exists():
            following = True
    except:
        pass

    if request.user == user:
        not_self_follow = False
    else:
        not_self_follow = True
    context = {
        'username': user,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following,
        'not_self_follow': not_self_follow,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    username = post.author
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user).order_by('-pub_date')
    posts_count = posts.count()
    thirty_symbols = post.text[:30]
    form_comment = CommentForm()
    post_comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'thirty_symbols': thirty_symbols,
        'posts_count': posts_count,
        'post_id': post_id,
        'form_comment': form_comment,
        'post_comments': post_comments,

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
    else:
        return redirect('posts:post_detail', post_id)


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

    posts_list = Post.objects.filter(author__following__user=user).order_by('-pub_date')
    page_obj =paginator(request, posts_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if user != author:
        if not Follow.objects.filter(
                user=User.objects.get(username=user),
                author=User.objects.get(username=username)
    ).exists():
            Follow.objects.create(
                user=User.objects.get(username=user),
                author=User.objects.get(username=username),
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
