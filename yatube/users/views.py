from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    """ Класс для создания формы регистрации нового пользователя."""
    form_class = CreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'users/signup.html'
