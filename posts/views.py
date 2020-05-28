from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, User, Comment
from .forms import PostForm, CommentForm


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
        form = PostForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            group = form.cleaned_data['group']
            new_post = Post.objects.create(
                text=text, 
                author=request.user,
                group=group)
            return redirect('index')
    form = PostForm()
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = User.objects.get(username=username)
    posts = author.author_posts.order_by('-pub_date')
    posts_cnt = posts.count()
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {
        'author': author, 
        'posts': posts,
        'paginator': paginator, 
        'page': page, 
        'posts_cnt': posts_cnt,
        })


def post_view(request, username, post_id):
    author = User.objects.get(username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    posts_cnt = author.author_posts.count()
    comments = post.post_comments.order_by('-created')
    comments_cnt = comments.count()
    form = CommentForm
    return render(request, 'post.html', {
        'author': author, 
        'post': post, 
        'posts_cnt': posts_cnt, 
        'comments': comments,
        'form': form,
        'comments_cnt': comments_cnt,
        })


@login_required
def add_comment(request, username, post_id):
    author = User.objects.get(username=username)
    post = Post.objects.get(pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            new_comment = Comment.objects.create(
                text=text, 
                author=request.user,
                post=post)
            return redirect('post_view', username, post_id)
    form = CommentForm()
    return render(request, 'post.html', {'form': form})       


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
                post.author = request.user
                post.save() 
                return redirect('post_view', username, post_id)
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

def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию, 
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
