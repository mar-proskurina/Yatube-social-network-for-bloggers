from django.contrib import admin
from .models import Comment, Follow, Post, Group


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',) 
    list_filter = ('pub_date',) 
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description') 
    search_fields = ('description',) 
    list_filter = ('title',) 
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post_id', 'post', 'text', 'created', 'author')
    search_fields = ('text',) 
    list_filter = ('author',) 
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user',) 
    list_filter = ('author',) 
    empty_value_display = '-пусто-'




admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)