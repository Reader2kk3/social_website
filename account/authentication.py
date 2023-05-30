from django.contrib.auth.models import User
from account.models import Profile

'''
    • backend: используемый для аутентификации пользователей бэкенд со-
    циальной аутентификации. Напомним, что вы добавили бэкенды соци-
    альной аутентификации в настроечный параметр AUTHENTICATION_BACK-
    ENDS проекта;
    • user: экземпляр класса User нового либо существующего пользователя,
    прошедшего аутентификацию.
'''
def create_profile(backend, user, *args, **kwargs):
    """
    Создать профиль пользователя для социальной аутентификации
    """
    Profile.objects.get_or_create(user=user)

class EmailAuthBackend:
    """
    Аутентифицировать посредством адреса электронной почты.
    """
    '''
    authenticate(): 
    извлекается пользователь с данным адресом электронной почты, 
    а пароль проверяется посредством встроенного метода check_password() 
    модели пользователя. Указанный метод хеширует пароль, чтобы сравнить 
    данный пароль с паролем, хранящимся в БД. 
    Отлавливаются два разных исключения, относящихся к набору
    запросов QuerySet: 
    - DoesNotExist (пользователь с данным адресом эл. почты не найден)
    - MultipleObjectsReturned (если найдено неск. user'ов с одним и тем же адресом эл.почты)
    '''
    '''
    get_user(): 
    пользователь извлекается по его id, указанному в параметре user_id. 
    Django использует аутентифицировавший пользователя бэкенд, чтобы извлечь объект User
    на время сеанса пользователя. 
    pk (сокращение от primary key) является уникальным идентификатором каждой записи в БД.
    Каждая модель Django имеет поле, которое служит ее первичным ключом. 
    По умолчанию первичным ключом является автоматически генерируемое поле id.
    Во встроенном в Django ORM-преобразователе первичный ключ тоже может называться pk.
    '''
    def authenticate(self, request, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


