from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Комментатор')
        cls.note = Note.objects.create(
            title='Тестовая новость', text='Просто текст.',
            slug='slug_test', author=cls.author
        )
        cls.reader = User.objects.create(username='Чтец')
        cls.note_2 = Note.objects.create(
            title='Тестовая новость 2', text='Просто текст 2.',
            slug='slug_test_2', author=cls.reader
        )
        cls.list_url = reverse('notes:list')
        cls.add_url = reverse('notes:add')
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))

    def test_authorized_client_note_list(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        response = self.client.get(self.list_url)
        object_list = response.context['object_list']
        # Определяем количество записей в списке.
        news_count = object_list.count()
        self.assertEqual(news_count, self.note.id)

    def test_authorized_client_note_add(self):
        self.client.force_login(self.author)
        response = self.client.get(self.add_url)
        self.assertIn('form', response.context)
        # Проверим, что объект формы соответствует нужному классу формы.
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_authorized_client_note_detail(self):
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        object = response.context['note']
        # Определяем количество записей в списке.
        note_id = object.id
        self.assertEqual(note_id, self.note.id)
