from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import SavedMovie
from django.contrib.auth import authenticate


class UserRegistrationForm(UserCreationForm):
    """
    Форма для регистрации нового пользователя.
    """
    email = forms.EmailField(required=True, help_text='Введите действующий адрес электронной почты.')

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')


class UserLoginForm(forms.Form):
    """
    Форма для авторизации пользователя.
    """
    username = forms.CharField(max_length=150, required=True, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Пароль')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_cache = None

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        self.user_cache = authenticate(username=username, password=password)
        if self.user_cache is None:
            raise forms.ValidationError("Неверное имя пользователя или пароль")
        return cleaned_data

    def get_user(self):
        return self.user_cache


class SaveMovieForm(forms.ModelForm):
    class Meta:
        model = SavedMovie
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введите название фильма'}),
        }

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'favorite_genre', 'bio', 'photo']