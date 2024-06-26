from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {"text": "Текст", "group": "Жанр", 'image': 'Картинка'}
        help_text = {"text": "Введите здесь текст поста",
                     "group": "Выберите жанр",
                     'image': 'Выберите фото'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст клмментария'}
        help_text = {'text': 'Введите здесь текст комментария'}
