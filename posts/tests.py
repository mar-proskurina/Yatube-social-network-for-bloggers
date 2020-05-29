from django.test import Client, TestCase, override_settings
from django.shortcuts import reverse
from posts.models import User, Post, Group 
from posts.forms import PostForm
import random
import time


class TestCache(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='masha_test', 
            password='584645'
        )
        self.client.force_login(self.user)


    def test_cache_main_page(self):
        resp1 = self.client.get('', follow=True)
        self.post = Post.objects.create(
            text='Just look at me', author=self.user)

        resp2 = self.client.get('', follow=True)
        self.assertNotContains(resp2, self.post.text, status_code=200, 
            msg_prefix ='Кэш не сработал, страница успела обновиться')

        time.sleep(21)
        resp3 = self.client.get('', follow=True)
        self.assertContains(resp3, self.post.text, status_code=200, 
            msg_prefix ='Новый пост на странице так и не появился')
        

class TestImg(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='masha_test', 
            password='584645'
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(title='Pretty Group', slug='pretty')
        
        self.post = Post.objects.create(
            text='Just look at me', author=self.user, group=self.group)
        

        with open('media/posts/puk.jpg', 'rb') as img:
            self.client.post(reverse('post_edit', 
                kwargs={
                    'username': self.user.username, 
                    'post_id': self.post.id
                    }),
                    {'text': 'edited', 
                    'image': img, 
                    'group': self.group.id
                    })



# проверяют, что срабатывает защита от загрузки файлов не-графических форматов
    def test_nonformat_img_protection(self):
        with open('media/posts/Django2.pdf', 'rb') as fake_img:
            resp4 = self.client.post(reverse('post_edit', kwargs={
                'username': self.user.username, 'post_id': self.post.id}), 
                {'text': 'edited', 'image': fake_img, 'group': self.group.id}
            )
        tag = '<img'
        
        #print(resp4.context.keys())
        #print('--------')
        #print(resp4.context['form'])
        #print('---fields-----')
        #print(resp4.context['form'].fields)
        #print('---files-----')
        #print(resp4.context['form'].files)
        #print('---validity-----')
        #print(resp4.context['form'].is_valid)
        #print('---items-in-errors-----')
        #print(resp4.context['form'].errors.items())
        
        #self.assertIn('image', resp4.context['form'].errors)
        self.assertNotContains(resp4, tag,
           msg_prefix=
           'На странице группы обнаружен Тэг <img>, файл как-то подгрузился')


    def test_post_page_has_img(self): 
        tag = '<img'
        resp = self.client.get(reverse('post_view', kwargs={
            'username': self.user.username, 'post_id': self.post.id}))
        self.assertContains(resp, tag,
            msg_prefix='Тэг <img> на странице поста не найден')


    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
        })
    def test_main_page_has_img(self):
        tag = '<img'
        resp1 = self.client.get('', follow=True) 
        self.assertContains(resp1, tag,
            msg_prefix='Тэг <img> на главной странице не найден')


    def test_profile_page_has_img(self):
        tag = '<img'
        resp2 = self.client.get(f'/{self.user.username}/', follow=True) 
        self.assertContains(resp2, tag,
            msg_prefix='Тэг <img> на странице профиля не найден')


    @override_settings(CACHES={'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
        })
    def test_group_page_has_img(self): 
        tag = '<img'
        resp3 = self.client.get(
            reverse('group_posts', kwargs={'slug': self.group.slug})) 
        self.assertContains(resp3, tag,
            msg_prefix='Тэг <img> на странице группы не найден')


class TestErrorPages(TestCase):

    def setUp(self):
        self.client = Client()


    def test_page_not_found(self):
        new_url = str(random.randint(0,12))
        response = self.client.get(f'{new_url}', follow=True)
        
        self.assertEqual(response.status_code, 404,
            msg='На ненайденную страницу сервер не вернул 404')



class TestPosts(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='masha_test', 
            password='584645'
        )
        #self.user.save()


    def test_profile_creation_upon_registration(self):
        resp = self.client.get(f'/{self.user.username}/', follow=True) 
        self.assertEqual(resp.status_code, 200, 
            msg='Профиль нового пользователя не был создан.') 


    def test_logged_in_user_can_post(self):
        self.client.force_login(self.user)
        self.post = Post.objects.create(
            text='Just look at me', author=self.user)
        response = self.client.get(f'/{self.user.username}/')
        self.assertEqual(response.status_code, 200, 
            msg='Не найдена страница пользователя.')
        self.assertEqual(len(response.context['posts']), 1,
            msg='Пост не был опубликован.')
        

    def test_not_logged_in_user_cannot_post(self):
        response = self.client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/',
            msg_prefix='Неавторизованный пользователь не был ' \
                'перенаправлен на страницу входа.')


    @override_settings(CACHES={'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }})
    def test_new_post_appears_on_all_pages(self):

        self.post = Post.objects.create(
            text='Just look at me', author=self.user)
        
        resp1 = self.client.get('', follow=True)
        self.assertContains(resp1, self.post.text, status_code=200, 
            msg_prefix ='Новый пост не найден на главной странице сайта.')
            
        resp2 = self.client.get(f'/{self.user.username}', 
            follow=True)
        self.assertContains(resp2, self.post.text, status_code=200, 
            msg_prefix='Новый пост не найден на странице профиля.')        
            
        resp3 = self.client.get(
            f'/{self.user.username}/{self.post.id}', follow=True)
        self.assertContains(resp3, self.post.text, status_code=200, 
            msg_prefix ='Новый пост не найден на странице самого поста.')             


    @override_settings(CACHES={'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }})
    def test_logged_in_user_can_edit_post(self):
        self.client.force_login(self.user)
        self.post = Post.objects.create(
            text='Just look at me', author=self.user)
        response = self.client.get(
            f'/{self.user.username}/{self.post.id}/edit/',
            follow=True)
        self.assertEqual(response.status_code, 200,
            msg='Пользователь не был перенаправлен ' \
                'на страницу редактирования.')        

        self.client.post(f'/{self.user.username}/{self.post.id}/edit/', 
            {'text': 'отредактировано'}) 

        #time.sleep(21)
        resp1 = self.client.get('', follow=True)
        self.assertContains(resp1, 'отредактировано', status_code=200, 
            msg_prefix ='Изменения в посте не отображаются '\
                'на главной странице сайта.')

        resp2 = self.client.get(f'/{self.user.username}', 
            follow=True)
        self.assertContains(resp2, 'отредактировано', status_code=200, 
            msg_prefix ='Изменения в посте не отображаются '\
                'на странице профиля автора.')        
            
        resp3 = self.client.get(
            f'/{self.user.username}/{self.post.id}', follow=True)
        self.assertContains(resp3, 'отредактировано', status_code=200, 
            msg_prefix ='Изменения в посте не отображаются на его странице.')   
