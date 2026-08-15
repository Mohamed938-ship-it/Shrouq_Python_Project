from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Post, Comment
from .forms import LoginForm, UserRegisterForm, PostForm, CommentForm

POSTS_PER_PAGE = 5


def home(request):
    paginator = Paginator(Post.objects.all(), POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)
    return render(request, "home.html", {"posts": posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={post.get_absolute_url()}")
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect("post_detail", pk=post.pk)
    else:
        form = CommentForm()
    return render(
        request, "post_detail.html", {"post": post, "comments": comments, "form": form}
    )


def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username} — your account is ready.")
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url or "home")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form, "next": request.GET.get("next", "")})


def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect("home")


@login_required
def add_post(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Post published.")
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, "add_post.html", {"form": form})


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        messages.error(request, "You can only edit your own posts.")
        return redirect(post.get_absolute_url())
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated.")
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)
    return render(request, "edit_post.html", {"form": form, "post": post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        messages.error(request, "You can only delete your own posts.")
        return redirect(post.get_absolute_url())
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
        return redirect("home")
    return render(request, "delete_post.html", {"post": post})
