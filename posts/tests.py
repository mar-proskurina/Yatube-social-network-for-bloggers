import random
import time
from django.test import Client, TestCase, override_settings
from django.shortcuts import reverse
from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User


class TestFollower(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_auth = User.objects.create_user(
            username='masha_test', 
            password='584645'
        )
        self.user_non_auth = User.objects.create_user(
            username='masha_test_2', 
            password='584645'
        )
        self.user_not_following = User.objects.create_user(
            username='masha_test_3', 
            password='584645'
        )
        self.client.force_login(self.user_auth)

        self.post = Post.objects.create(
            text='Just look at me', author=self.user_auth)


    def test_auth_user_can_follow(self):

        resp1 = self.client.post(reverse('profile_follow', kwargs={
            'username': self.user_non_auth.username, 
            }), follow=True) 
        
        follow_amt = Follow.objects.filter(user=self.user_auth).count()
        
        self.assertEqual(follow_amt, 1,
            msg='Тестовый юзер не подписался на автора.')

        resp2 = self.client.post(reverse('profile_unfollow', kwargs={
            'username': self.user_non_auth.username, 
            }), follow=True) 
        
        follow_amt_2 = Follow.objects.filter(user=self.user_auth).count()
        
        self.assertEqual(follow_amt_2, 0,
            msg='Тестовый юзер не отписался от автора.')


    def test_new_post_appears_in_follow_page_of_the_follower(self):
        self.post = Post.objects.create(
            text='Just look at me', author=self.user_non_auth
            )
        
        self.client.post(reverse('profile_follow', kwargs={
            'username': self.user_non_auth.username, 
            }), follow=True) 
        resp3 = self.client.get('/follow', follow=True)

        self.assertContains(resp3, self.post.text, status_code=200, 
            msg_prefix='Новый пост не найден на странице подписок.')   
        

    def test_new_post_does_not_appear_in_follow_page_of_non_followers(self):
        self.post = Post.objects.create(
            text='Just look at me', author=self.user_non_auth
            )
        self.user_not_following = Client()
        resp4 = self.user_not_following.get('/follow', follow=True)
        self.assertNotContains(resp4, self.post.text, status_code=200, 
            msg_prefix='Новый пост обнаружен на странице подписок.')


class TestComments(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_auth = User.objects.create_user(
            username='masha_test', 
            password='584645'
        )
        self.user_non_auth = User.objects.create_user(
            username='masha_test_2', 
            password='584645'
        )
        self.client.force_login(self.user_auth)
        self.post = Post.objects.create(
            text='Just look at me', author=self.user_auth)

        self.user_non_auth = Client()


    def test_auth_user_can_comment(self):

        self.comment = Comment.objects.create(post=self.post, 
            author=self.user_auth,
            text='Just look at me')
        resp1 = self.client.get(reverse('post_view', kwargs={
            'username': self.user_auth.username, 
            'post_id': self.post.id}), 
            follow=True)

        self.assertContains(resp1, 'Just look at me', status_code=200, 
            msg_prefix='На страинце поста не найден новый комментарий')
            

    def test_non_auth_user_cannot_comment(self):

        resp2 = self.user_non_auth.get(reverse('add_comment', kwargs={
            'username': self.user_auth.username, 
            'post_id': self.post.id}), 
            follow=True)
        self.assertRedirects(
            resp2, 
            f'/auth/login/?next=/{self.user_auth}/{self.post.id}/comment/',
            msg_prefix=('Неавторизованный пользователь не был ' 
                'перенаправлен на страницу входа.')
        )


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
            msg_prefix='Кэш не сработал, страница успела обновиться')

        time.sleep(21)
        resp3 = self.client.get('', follow=True)
        self.assertContains(resp3, self.post.text, status_code=200, 
            msg_prefix='Новый пост на странице так и не появился')
        

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


    def test_nonformat_img_protection(self):
        with open('media/posts/Django2.pdf', 'rb') as fake_img:
            resp4 = self.client.post(reverse('post_edit', kwargs={
                'username': self.user.username, 'post_id': self.post.id}), 
                {'text': 'edited', 'image': fake_img, 'group': self.group.id}
            )

        self.assertIn('image', resp4.context['form'].errors,
           msg='Форма не отловила ошибку в изображении и приняла картинку.')
        # хочу сделать через форм еррор, вот так print(resp4.context['form'].errors.items())
        # я нашла ошибку, но почему-то тест на нее не реагирует, в слаке не получилось 
        # решить этот вопрос, может, у вас будут идеи?
        #self.assertFormError(resp4, 'form', 'image', 
        #    'Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.')

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
            msg_prefix=('Неавторизованный пользователь не был '
                'перенаправлен на страницу входа.'))


    @override_settings(CACHES={'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }})
    def test_new_post_appears_on_all_pages(self):

        self.post = Post.objects.create(
            text='Just look at me', author=self.user)
        
        resp1 = self.client.get('', follow=True)
        self.assertContains(resp1, self.post.text, status_code=200, 
            msg_prefix='Новый пост не найден на главной странице сайта.')
            
        resp2 = self.client.get(f'/{self.user.username}', 
            follow=True)
        self.assertContains(resp2, self.post.text, status_code=200, 
            msg_prefix='Новый пост не найден на странице профиля.')        
            
        resp3 = self.client.get(
            f'/{self.user.username}/{self.post.id}', follow=True)
        self.assertContains(resp3, self.post.text, status_code=200, 
            msg_prefix='Новый пост не найден на странице самого поста.')             


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
            msg=('Пользователь не был перенаправлен ' 
                'на страницу редактирования.'))       

        self.client.post(f'/{self.user.username}/{self.post.id}/edit/', 
            {'text': 'отредактировано'}) 

        resp1 = self.client.get('', follow=True)
        self.assertContains(resp1, 'отредактировано', status_code=200, 
            msg_prefix=('Изменения в посте не отображаются '
                'на главной странице сайта.'))

        resp2 = self.client.get(f'/{self.user.username}', 
            follow=True)
        self.assertContains(resp2, 'отредактировано', status_code=200, 
            msg_prefix=('Изменения в посте не отображаются '
                'на странице профиля автора.'))      
            
        resp3 = self.client.get(
            f'/{self.user.username}/{self.post.id}', follow=True)
        self.assertContains(resp3, 'отредактировано', status_code=200, 
            msg_prefix='Изменения в посте не отображаются на его странице.')   
