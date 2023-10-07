from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Follow, Group, Post, User
from .utils import paginator


def index(request):
    post_list = Post.objects.select_related('author')
    page_obj = paginator(request, post_list)
    return render(request,
                  'posts/index.html',
                  {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator(request, post_list)
    return render(request,
                  'posts/group_list.html',
                  {'group': group, 'page_obj': page_obj})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator(request, post_list)
    following = (request.user.is_authenticated) and (
        request.user != author) and Follow.objects.filter(
        user=request.user, author=author).exists()
    return render(request,
                  'posts/profile.html',
                  {'author': author,
                   'page_obj': page_obj,
                   'following': following})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    return render(request,
                  'posts/post_detail.html',
                  {'post': post, 'form': form, 'comments': comments})


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    return render(request,
                  'posts/create_post.html',
                  {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': True})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    post.delete()
    return redirect('posts:profile', username=request.user.username)


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
    follow_list = Follow.objects.select_related('user').filter(
        user=request.user)
    author_list = follow_list.values('author')
    post_list = Post.objects.select_related('author').filter(
        author__in=author_list)
    page_obj = paginator(request, post_list)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author).all()
    follower.delete()
    return redirect('posts:profile', username=author.username)
