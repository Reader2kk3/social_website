from django import forms
from .models import Image

from django.core.files.base import ContentFile
from django.utils.text import slugify
import requests

class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['title', 'url', 'description']
        widgets = {'url': forms.HiddenInput,}

    '''
    1) значение поля url извлекается путем обращения к словарю clean_data
    экземпляра формы;
    2) URL-адрес разбивается на части, чтобы проверить наличие валидного
    расширения у файла. Если расширение невалидно, то выдается ошибка
    ValidationError, и экземпляр формы не валидируется.
    '''
    def clean_url(self):
        url = self.cleaned_data['url']
        valid_extensions = ['jpg', 'jpeg', 'png']
        extension = url.rsplit('.', 1)[1].lower()
        if extension not in valid_extensions:
            raise forms.ValidationError('The given URL does not match valid image extensions.')
        return url

    # Переопределение метода save() класса ModelForm
    '''
    1. Новый экземпляр изображения создается путем вызова метода save()
    формы с commit=False.
    2. URL-адрес изображения извлекается из словаря clean_data формы.
    3. Имя изображения генерируется путем комбинирования названия изо-
    бражения с изначальным расширением файла изображения.
    4. Библиотека Python requests используется для скачивания изображе-
    ния путем отправки HTTP-запроса методом GET с использованием URL-
    адреса изображения. Ответ сохраняется в объекте response.
    5. Вызывается метод save() поля image, передавая ему объект ContentFile,
    экземпляр которого заполнен содержимым скачанного файла. Таким
    путем файл сохраняется в каталог media проекта. Параметр save=False
    передается для того, чтобы избежать сохранения объекта в базе данных.
    6. Для того чтобы оставить то же поведение, что и в изначальном мето-
    де save() модельной формы, форма сохраняется в базе данных только
    в том случае, если параметр commit равен True.
    '''
    def save(self, force_insert=False, force_update=False, commit=True):
        image = super().save(commit=False)
        image_url = str(self.cleaned_data['url'])
        name = slugify(image.title)
        extension = image_url.rsplit('.', 1)[1].lower()
        image_name = f'{name}.{extension}'
        # скачать изображение с данного URL-адреса
        response = requests.get(image_url)
        image.image.save(image_name, ContentFile(response.content), save=False)
        
        if commit:
            image.save()

        return image
        
       