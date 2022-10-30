from django.core.paginator import Paginator

POST_NUMB: int = 10


def my_paginator(request, items_list):
    paginator = Paginator(items_list, POST_NUMB)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
