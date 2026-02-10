from django.shortcuts import redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm


class CustomLoginView(LoginView):
    template_name = 'login_page.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('sensor:home')


class CustomLogoutView(LogoutView):
    """Class-based logout that forces redirect to login page"""
    next_page = 'core:login'
    http_method_names = ['get', 'post', 'head', 'options']

    def dispatch(self, request, *args, **kwargs):
        # Ensure immediate redirect without rendering admin template
        logout(request)
        return redirect(self.next_page)


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'register_page.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)
        return redirect('sensor:home')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('sensor:home')
        return super().get(request, *args, **kwargs)

