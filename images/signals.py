from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Image

# Сперва, используя декоратор receiver(), в качестве функции-получателя регистрируется
# функция users_like_changed. Она привязывается к сигналу m2m_changed.
# Затем эта функция соединяется с Image.users_like.through, чтобы функция 
# вызывалась только в том случае, если сигнал m2m_changed был запущен этим отправителем.
@receiver(m2m_changed, sender=Image.users_like.through)
def users_like_changed(sender, instance, **kwargs):
    instance.total_likes = instance.users_like.count()
    instance.save()
    