from django import forms
from django.contrib.auth.models import User
from .models import Profile

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    '''
    Мы добавили валидацию поля электронной почты, которая не позволяет
    пользователям регистрироваться с уже существующим адресом электронной
    почты. Мы формируем набор запросов QuerySet, чтобы свериться, нет ли
    существующих пользователей с одинаковым адресом электронной почты.
    Мы проверяем наличие результатов посредством метода exists(). Метод ex-
    ists() возвращает True, если набор запросов QuerySet содержит какие-либо
    результаты, и False в противном случае.
    '''
    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Email already in use.')
        return data


# UserEditForm позволит пользователям редактировать свое имя, фамилию и адрес
# электронной почты, которые являются атрибутами встроенной в Django модели User
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    '''
    В данном случае мы добавили валидацию поля email, чтобы пользователи
    не могли изменять свой бывший адрес электронной почты на существую-
    щий адрес электронной почты другого пользователя. Мы исключаем теку-
    щего пользователя из набора запросов. В противном случае текущий адрес
    электронной почты пользователя будет считаться существующим адресом
    электронной почты, и форма не пройдет валидацию.
    '''
    def clean_email(self):
        data = self.cleaned_data['email']
        qs = User.objects.exclude(id=self.instance.id).filter(email=data)
        
        if qs.exists():
            raise forms.ValidationError(' Email already in use.')
        return data


# ProfileEditForm позволит пользователям редактировать данные профиля, сохраненные
# в конкретно-прикладной модели Profile. Пользователи смогут редактировать
# дату своего рождения и закачивать изоражение на сайт в качестве фотоснимка профиля.
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['date_of_birth', 'photo']
