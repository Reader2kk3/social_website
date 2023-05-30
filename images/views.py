from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ImageCreateForm
from django.shortcuts import get_object_or_404
from .models import Image
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from actions.utils import create_action

import redis
from django.conf import settings

# соединить с redis
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


@login_required
@require_POST
def image_like(request):
    image_id = request.POST.get('id')
    action = request.POST.get('action')
    if image_id and action:
        try:
            image = Image.objects.get(id=image_id)
            if action == 'like':
                image.users_like.add(request.user)
                create_action(request.user, 'likes', image)
            else:
                image.users_like.remove(request.user)
            return JsonResponse({'status': 'ok'})
        except Image.DoesNotExist:
            pass
    return JsonResponse({'status': 'error'})

'''
В этом представлении используется команда incr, которая увеличивает
значение данного ключа на 1. Если ключ не существует, то команда incr его
создает. Метод incr() возвращает окончательное значение ключа после вы-
полнения операции. Его значение сохраняется в переменной total_views, ко-
торая затем передается в контекст шаблона. Ключ Redis создается, используя
формат object-type:id:field (например, image:33:id).


Команда zincrby() используется для сохранения просмотров изображений
в сортированном множестве с ключом image:ranking. В нем будут храниться
id изображения и соответствующий балл, равный 1, который будет добавлен
к общему баллу этого элемента сортированного множества. Такой подход
позволит отслеживать все просмотры изображений в глобальном масштабе
и иметь сортированное множество, упорядоченное по общему числу про-
смотров.
'''
def image_detail(request, id, slug):
    image = get_object_or_404(Image, id=id, slug=slug)
    # увеличить общее число просмотров изображения на 1
    total_views = r.incr(f'image:{image.id}:views')
    # увеличить рейтинг изобажения на 1
    r.zincrby('image_ranking', 1, image.id)
    context = {'section': 'images', 'image': image, 'total_views': total_views}
    return render(request, 'images/detail.html', context)


'''
Представление image_ranking работает следующим образом.
1. Для получения элементов сортированного множества используется ко-
манда zrange(). Эта команда ожидает конкретно-прикладной диапазон
в соответствии с самым низким и самым высоким баллами. Используя
0 в качестве наименьшего значения и –1 в качестве наибольшего, базе
данных Redis сообщается, что нужно вернуть все элементы сортирован-
ного множества. Для извлечения элементов, упорядоченных по убыва-
нию балла, также указывается параметр desc=True. Наконец, результа-
ты нарезаются, используя [:10], чтобы получить первые 10 элементов
с наивысшим баллом.
2. Создается список возвращаемых ИД изображений и сохраняется в пе-
ременной image_ranking_ids в виде списка целых чисел. По этим иден-
тификаторам извлекаются объекты Image, и с помощью функции list()
запрос принудительно исполняется. Важно вызвать принудительное
исполнение набора запросов QuerySet, потому что для него будет ис-
пользоваться списковый метод sort() (на этом этапе вместо набора
запросов QuerySet нужен список объектов).
3. Объекты Image сортируются по индексу их появления в рейтинге изо-
бражений. Теперь в шаблоне можно использовать список most_viewed,
чтобы отобразить 10 самых просматриваемых изображений.
'''
@login_required
def image_ranking(request):
    # получить словарь рейтинга изображений
    image_ranking = r.zrange('image_ranking', 0, -1, desc=True)[:10]
    image_ranking_ids = [int(id) for id in image_ranking]
    # получить наиболее просматриваемые изображения
    most_viewed = list(Image.objects.filter(id__in=image_ranking_ids))
    most_viewed.sort(key=lambda x: image_ranking_ids.index(x.id))

    context = {'section': 'images', 'most_viewed': most_viewed}
    return render(request, 'images/rating.html', context)




'''
1. Для создания экземпляра формы необходимо предоставить начальные
данные через HTTP-запрос методом GET. Эти данные будут состоять
из атрибутов url и title изображения с внешнего веб-сайта. Оба па-
раметра будут заданы в запросе GET букмарклетом JavaScript, который
мы создадим позже. Пока же можно допустить, что эти данные будут
иметься в запросе.
2. После того как форма передана на обработку с помощью HTTP-запроса
методом POST, она валидируется методом form.is_valid(). Если данные
в форме валидны, то создается новый экземпляр Image путем сохране-
ния формы методом form.save(commit=False). Новый экземпляр в базе
данных не сохраняется, если commit=False.
3. В новый экземпляр изображения добавляется связь с текущим пользо-
вателем, который выполняет запрос: new_image.user = request.user. Так
мы будем знать, кто закачивал каждое изображение.
4. Объект Image сохраняется в базе данных.
5. Наконец, с помощью встроенного в Django фреймворка сообщений
создается сообщение об успехе, и пользователь перенаправляется на
канонический URL-адрес нового изображения. Мы еще не реализовали
метод get_absolute_url() модели Image; мы сделаем это позже.
'''
@login_required
def image_create(request):
    if request.method == 'POST':
        # форма отправлена
        form = ImageCreateForm(data=request.POST)
        if form.is_valid():
            # данные в форме валидны
            cd = form.cleaned_data 
            new_image = form.save(commit=False)
            # назначить текущего пользователя элементу  
            new_image.user = request.user
            new_image.save()
            create_action(request.user, 'bookmarked image', new_image)
            messages.success(request, 'Image added successfully')
            # перенаправить к представлению детальной
            # информации о только что созданном элементе
            return redirect(new_image.get_absolute_url())
    else:
        # скомпоновать форму с данными,
        # предоставленными букмарклетом методом GET
        form = ImageCreateForm(data=request.GET)

    context = {'section': 'images', 'form': form}
    return render(request, 'images/create.html', context)

    
@login_required
def image_list(request):
    images = Image.objects.all()
    paginator = Paginator(images, 8)
    page = request.GET.get('page')
    images_only = request.GET.get('images_only')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # Если страница не является целым числом,
            # то доставить первую страницу
        images = paginator.page(1)
    except EmptyPage:
        if images_only:
            # Если AJAX-запрос и страница вне диапазона,
            # то вернуть пустую страницу
            return HttpResponse('') 
        # Если страница вне диапазона,
        # то вернуть последнюю страницу результатов
        images = paginator.page(paginator.num_pages)

    if images_only:
        context = {'section': 'images', 'images': images}
        return render(request, 'images/list_images.html', context)

    context = {'section': 'images', 'images': images}
    return render(request, 'images/list.html', context)