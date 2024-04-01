from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    NOTE_TITLE = 'Тестовая записка'
    NOTE_TEXT = 'Просто текст.'
    NOTE_SLUG = 'slug_test'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Комментатор')
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Данные для POST-запроса при создании записки.
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG
        }
        cls.reader = User.objects.create(username='Чтец')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.url = reverse('notes:add')
        cls.url_to_done = reverse('notes:success')

    def test_anonymous_user_cant_create_comment(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом записки.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество комментариев.
        comments_count = Note.objects.count()
        # Ожидаем, что записки в базе нет - сравниваем с нулём.
        self.assertEqual(comments_count, 0)

    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.author_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с записками.
        self.assertRedirects(response, self.url_to_done)
        # Считаем количество записок.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть одна записка.
        self.assertEqual(notes_count, 1)
        # Получаем объект записки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты записки совпадают с ожидаемыми.
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.slug, self.NOTE_SLUG)


class TestNoteEditDelete(TestCase):

    NOTE_TITLE = 'Тестовая записка'
    NEW_NOTE_TITLE = 'Новая Тестовая записка'
    NOTE_TEXT = 'Просто текст.'
    NEW_NOTE_TEXT = 'Новый Просто текст'
    NOTE_SLUG = 'slug_test'
    NEW_NOTE_SLUG = 'new_slug_test'

    @classmethod
    def setUpTestData(cls):

        cls.author = User.objects.create(username='Комментатор')
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE, text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG, author=cls.author
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG
        }
        cls.reader = User.objects.create(username='Чтец')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.url_to_done = reverse('notes:success')

    def test_author_can_delete_note(self):
        # От имени автора записки отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу с записками.
        self.assertRedirects(response, self.url_to_done)
        # Считаем количество записок в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль записок в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что записка по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        # Выполняем запрос на редактирование от имени автора записки.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.url_to_done)
        # Обновляем объект записки.
        self.note.refresh_from_db()
        # Проверяем, что текст записки соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект записки.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)
