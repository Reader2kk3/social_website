from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

class Image(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='images_created', on_delete=models.CASCADE)
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='images_liked', blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    url = models.URLField(max_length=2000)
    image = models.ImageField(upload_to='images/%Y/%m/%d/')
    description = models.TextField(blank=True)
    total_likes = models.PositiveIntegerField(default=0)
    created = models.DateField(auto_now_add=True)

    class Meta:
        # индекс базы данных в убывающем порядке по полю created
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['-total_likes']),
        ]
        ordering = ['-created']

    def __str__(self):
        return self.title

    # Если при сохранении объекта Image поле slug является пустым, то slug ге-
    # нерируется автоматически из поля title изображения с помощью функции
    # slugify(). Затем объект сохраняется. Благодаря автоматическому генериро-
    # ванию слага из заголовка пользователям не придется указывать слаг, когда
    # они делятся изображениями на сайте.
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('images:detail', args=[self.id, self.slug])