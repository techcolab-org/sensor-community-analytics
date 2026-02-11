from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import CustomPasswordChangeForm, CustomUserCreationForm


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
    success_url = reverse_lazy('core:login')

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


@login_required
def change_password(request):
    """
    View for changing user password
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update session to prevent logout after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('core:change_password')  # Or redirect to profile/dashboard
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'change_password.html', {
        'form': form
    })