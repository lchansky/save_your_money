from django.contrib import messages
from django.shortcuts import redirect

from .models import *


def check_permissions(model, redirect_page='home'):
    """Декоратор, кидает message.error и redirect на redirect_page, если объект модели model
    с первичным ключом pk не принадлежит пользователю request.user.
    Срабатывает, если пользователь пытается удалить/редактировать/просмотреть
    объект модели model, который ему не принадлежит"""
    def my_decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]
            pk = kwargs['pk']
            if model.objects.filter(pk=pk, user=request.user).count() == 0:
                messages.error(request, 'У вас нет прав доступа!')
                return redirect(redirect_page)
            return func(*args, **kwargs)
        return wrapper
    return my_decorator