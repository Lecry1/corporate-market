from adverts.models import Advert
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Review

User = get_user_model()


def get_reviews_about_user(request, user_id):
    # Получить все отзывы, где пользователь — получатель (отзывы о пользователе)
    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(to_user=user).select_related('from_user', 'advert')

    context = {
        'user': user,
        'reviews': reviews,
        'count': reviews.count(),
    }
    return render(request, 'reviews/about_user.html', context)


def get_reviews_by_user(request, user_id):
    # Получить все отзывы, которые пользователь написал (его активность)
    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(from_user=user).select_related('to_user', 'advert')

    context = {
        'user': user,
        'reviews': reviews,
    }
    return render(request, 'reviews/by_user.html', context)


def get_reviews_for_advert(request, advert_id):
    # Получить все отзывы по конкретному объявлению
    advert = get_object_or_404(Advert, id=advert_id)
    reviews = Review.objects.filter(advert=advert).select_related('from_user', 'to_user')

    context = {
        'advert': advert,
        'reviews': reviews,
    }
    return render(request, 'reviews/for_advert.html', context)


def get_user_rating(request, user_id):
    # Получить средний рейтинг пользователя и количество отзывов

    user = get_object_or_404(User, id=user_id)

    stats = Review.objects.filter(to_user=user).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id'),
        positive_count=Count('id', filter=Q(rating__gte=4)),
        negative_count=Count('id', filter=Q(rating__lte=2)),
    )

    # Округление до десятых
    if stats['avg_rating']:
        stats['avg_rating'] = round(stats['avg_rating'], 1)

    context = {
        'user': user,
        'stats': stats,
    }
    return render(request, 'reviews/user_rating.html', context)


def get_reviews_to_seller(request, user_id):
    # Получить все отзывы о пользователе как о продавце (через его объявления)
    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(advert__seller=user).select_related('from_user', 'advert')

    context = {
        'user': user,
        'reviews': reviews,
        'title': f'Отзывы о продавце {user.username}',
    }
    return render(request, 'reviews/about_user.html', context)


def get_recent_reviews(request, user_id):
    # Получить 10 самых свежих отзывов о пользователе
    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(to_user=user).order_by('-created_at')[:10]

    context = {
        'user': user,
        'reviews': reviews,
    }
    return render(request, 'reviews/recent.html', context)


#  --- API (JSON) версия для микросервисной архитектуры ---


def api_user_reviews(request, user_id):
    # API-эндпоинт: получить все отзывы о пользователе в JSON
    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(to_user=user).select_related('from_user', 'advert')

    data = {
        'user_id':
        user.id,
        'username':
        user.username,
        'total_reviews':
        reviews.count(),
        'avg_rating':
        reviews.aggregate(Avg('rating'))['rating__avg'],
        'reviews': [{
            'id': r.id,
            'from_user': r.from_user.username,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat(),
            'flag': r.get_flag_display(),
            'advert_title': r.advert.title,
        } for r in reviews]
    }
    return JsonResponse(data)
