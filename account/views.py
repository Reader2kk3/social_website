from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm

from django.contrib.auth.decorators import login_required
from .models import Profile
from django.contrib import messages

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from actions.utils import create_action
from actions.models import Action

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Contact

# Декоратор login_required проверяет аутентификацию текущего пользователя.
# Если пользователь аутентифицирован, то оно исполняет декорированное представление,
# если пользователь не аутентифицирован, то оно перенаправляет пользователя на URL-адрес входа
# с изначально запрошенным URL-адресом в качестве GET-параметра с именем next.
@login_required
def dashboard(request):
    # По умолчанию показать все действия
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list('id', flat=True)

    if following_ids:
        # Если пользователь подписан на других,
        # то извлечь только их действия
        actions = actions.filter(user_id__in=following_ids)

    # select_related - это транслируется в один более сложный набор запросов,
    # но зато позволяет избегать дополнительных запросов при доступе к связанным объектам.

    # prefetch_related, который в дополнение к взаимосвязям, поддерживаемым методом 
    # select_related(), успешно работает для взаимосвязей многие-ко-многим и многие-к-одному.
    actions = actions.select_related('user', 'user__profile')[:10]\
                        .prefetch_related('target')[:10]

    context = {'section': 'dashboard','actions': actions}
    return render(request, 'account/dashboard.html', context)

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Создать новый объект пользователя,
            # но пока не сохранять его
            new_user = user_form.save(commit=False)
            # Установить выбранный пароль
            # set_password - хеширует пароль перед его сохранением в БД
            new_user.set_password(user_form.cleaned_data['password'])
            # Сохранить объект User
            new_user.save()
            # Создать профиль пользователя
            Profile.objects.create(user=new_user)
            create_action(new_user, 'has created an account')
            return render(request, 'account/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()

    return render(request, 'account/register.html', {'user_form': user_form})

@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, 
        data=request.POST, files=request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating your profile')

    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'account/edit.html', context)

# Представление user_list получает всех активных пользователей.
@login_required
def user_list(request):
    users = User.objects.filter(is_active=True)
    context =  {'section': 'people', 'users': users}
    return render(request, 'account/user/list.html', context)

# извлекаются активные пользователя с переданным пользовательским именем (username)
@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    context = {'section': 'people', 'user': user}
    return render(request, 'account/user/detail.html', context)


@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user, user_to=user)
                create_action(request.user, 'is following', user)
            else:
                Contact.objects.filter(user_from=request.user, user_to=user).delete()
                return JsonResponse({'status':'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status':'error'})

    return JsonResponse({'status':'error'})


def user_login(request):
    if request.method == 'POST':
        # Cоздается экземпляр формы с переданными данными
        form = LoginForm(request.POST)

        # Валидация формы
        if form.is_valid():
            # cleaned_data - валидация пользовательского ввода
            cd = form.cleaned_data
            # Пользователь аутентифицируется по БД методом authenticate()
            user = authenticate(request, username=cd['username'], password=cd['password'])
            '''
            Указанный метод принимает объект request, параметры username и password и возвращает
            объект User, если пользователь был успешно аутентифицирован, либо
            None в противном случае. Если пользователь не был успешно аутентифицирован, 
            то возвращается сырой ответ HttpResponse с сообщением
            Invalid login (Недопустимый логин)
            '''

            # Если пользователь успешно аутентифицирован
            
            if user is not None:
                # То статус пользователя проверяется путем обращения к атрибуту is_active
                if user.is_active:
                    # Если пользователь активен, то он входит в систему. 
                    # Пользователь задается в сеансе путем вызова метода login()
                    login(request, user)
                    # return 'Аутентификация прошла успешно'
                    return HttpResponse('Authenticated successfully')

                # Если пользователь не активен, то возвращается HttpResponse
                # с сообщением Disabled account (Отключенная учетная запись)
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()

    context = {'form': form}
    return render(request, 'account/login.html', context)
