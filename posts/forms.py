from django.forms import ModelForm
from posts.models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post 
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа'
            }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = {'text'}
        labels = {
            'text': 'Комментарий',
            }
        