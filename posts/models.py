from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Follow(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='follower',
        null=True,
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='following',
        null=True, 
    )

    def __str__(self):
        return f'follower - {self.user} following {self.author}.'


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=40, unique=True)
    description = models.TextField()

    def __str__(self):
        return f'{self.title}'


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='author_posts'
    )
    group = models.ForeignKey(
        Group, 
        on_delete=models.SET_NULL, 
        related_name='group_posts', 
        null=True, 
        blank=True
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return f'{self.author}: {self.text[:20]}...'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE, 
        related_name='post_comments'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='author_comments'
    )
    text = models.TextField()
    created = models.DateTimeField('date created', auto_now_add=True)

    def __str__(self):
        return f'{self.created}: {self.text}'
