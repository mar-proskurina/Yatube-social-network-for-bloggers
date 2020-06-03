from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .models import Comment, Follow, Group, Post, User
from .forms import CommentForm, PostForm


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {
        'page': page, 'paginator': paginator
        })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_posts.order_by('-pub_date')
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {
        'page': page, 'paginator': paginator,
        'group': group
        })


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, 
                files=request.FILES or None)
        if form.is_valid():
            new_post = form.save(commit=False) 
            new_post.author = request.user 
            new_post.save()
            return redirect('index')
    form = PostForm()
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = User.objects.get(username=username)
    posts = author.author_posts.order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follower=None
    if request.user.is_authenticated:
        follower = author.following.filter(user=request.user)
    return render(request, 'profile.html', {
        'author': author, 
        'posts': posts,
        'paginator': paginator, 
        'page': page, 
        'follower': follower
        })


def post_view(request, username, post_id):
    author = User.objects.get(username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    posts_cnt = author.author_posts.count()
    comments = post.post_comments.order_by('-created')

    form = CommentForm()
    return render(request, 'post.html', {
        'author': author, 
        'post': post, 
        'posts_cnt': posts_cnt, 
        'comments': comments,
        'form': form,
        })


@login_required
def add_comment(request, username, post_id):
    author = User.objects.get(username=username)
    post = Post.objects.get(pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST or None)
        if form.is_valid():
            new_comment = form.save(commit=False) 
            new_comment.author = request.user 
            new_comment.post = post
            new_comment.save()
    form = CommentForm()
    return redirect('post_view', username, post_id) 


@login_required
def post_edit(request, username, post_id):
    user = User.objects.get(username=username)
    post = Post.objects.get(pk=post_id)
    if user == post.author:
        if request.method == 'POST':
            form = PostForm(
                request.POST or None, 
                files=request.FILES or None, 
                instance=post
                )
            if form.is_valid():
                post = form.save(commit=False)
                post.save() 
                return redirect('post_view', username, post_id)
            else: 
                render(request, 'new.html', {'form': form})
        form = PostForm(instance=post)
        return render(request, 'new.html', {
            'form': form, 
            'post_id': post_id, 
            'post': post
            })
    else:
        author = post.author
        return render(request, 'post.html', {
            'author': author, 
            'post': post
            })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follower_status = Follow.objects.filter(
        user=request.user, author=author
        ).exists()
    if not follower_status:
        if request.user != author:
            Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower_status = Follow.objects.filter(
        user=request.user, author=author
        ).exists()
    if follower_status:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username)
            
    
@login_required
def follow_index(request):
    all_follows = Follow.objects.filter(user=request.user)
    authors = (i.author for i in all_follows)
    post_list = Post.objects.filter(author__in=authors).order_by('-pub_date')

    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'follow.html', {
        'page': page, 'paginator': paginator,
        })


def page_not_found(request, exception):
    return render(request, 'misc/404.html', 
        {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
