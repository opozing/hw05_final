from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import PAG_CONST

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


def index(request):
    post_objects = Post.objects.all()
    paginator = Paginator(post_objects, PAG_CONST)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page,
                                          "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_objects = group.posts.all()
    paginator = Paginator(post_objects, PAG_CONST)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"group": group,
               "page": page,
               "paginator": paginator}
    return render(request, "group.html", context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        new_form = form.save(commit=False)
        new_form.author = request.user
        form.save()
        return redirect("posts:index")
    return render(request, "new_post.html", {"form": form})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id,
                             author__username=username)
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        new_form = form.save(commit=False)
        new_form.author = request.user
        new_form.post = post
        form.save()
    return redirect("posts:post", username=username, post_id=post_id)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    paginator = Paginator(author_posts, PAG_CONST)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()

    context = {
        "author": author,
        "page": page,
        "paginator": paginator,
        "following": following,
    }
    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id,
                             author__username=username)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        "form": form,
        "post": post,
        "comments": comments,
        "author": post.author,
    }
    return render(request, "post.html", context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id,
                             author__username=username)
    if request.user.username != username:
        return redirect("posts:post", username=username, post_id=post_id)

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("posts:post", username=username, post_id=post_id)

    context = {
        "form": form,
        "post": post,
        "edit": True,
    }
    return render(request, "new_post.html", context)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path},
                  status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    """страница с постами авторов , на которых подписан текущий юзер."""
    post_objects = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_objects, PAG_CONST)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator,
    }
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    author = get_object_or_404(User, username=username)
    if request.user.username != username:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:profile", username=username)
