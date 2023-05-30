from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)

    def __str__(self):
        return f'Profile of {self.user.username}'


# • user_from: внешний ключ (ForeignKey) для пользователя, который создает взаимосвязь;
# • user_to: внешний ключ (ForeignKey) для пользователя, на которого есть подписка;
# • created: поле DateTimeField с параметром auto_now_add=True для хранения 
# времени создания взаимосвязи.

# Система подписок
class Contact(models.Model):
    user_from = models.ForeignKey('auth.User', related_name='rel_from_set', on_delete=models.CASCADE)
    user_to = models.ForeignKey('auth.User', related_name='rel_to_set', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['-created']),]
        ordering = ['-created']
    
    def __str__(self):
        return f'{self.user_from} follows {self.user_to}'


# Добавить следующее поле в User динамически
# Метод add_to_class() моделей Django применяется для того, 
# чтобы динамически подправлять модель User
# В идеале существующую модель User изменять не следует.
user_model = get_user_model()
# В данном же случае устанавливается параметр symmetrical=False,
# чтобы определить несимметричную взаимосвязь (если я на вас подписываюсь,
#  то это не означает, что вы автоматически подписываетесь на меня).
user_model.add_to_class('following', models.ManyToManyField('self', through=Contact,
                        related_name='followers', symmetrical=False))
