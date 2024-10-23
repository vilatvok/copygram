from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, FormView
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

from django_celery_beat.models import PeriodicTask

from two_factor.views.core import SetupView, LoginView
from two_factor.views.profile import DisableView

from users.models import User
from users.forms import CustomPasswordResetForm, CustomUserCreationForm
from users.utils import check_token, send_reset_email


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'

    def form_invalid(self, form):
        email = form.data['email']
        user = User.objects.filter(email=email)
        if user.exists():
            messages.info(
                request=self.request,
                message="You've already fill this form, check email",
            )
            return redirect(self.get_success_url())
        else:
            return super().form_invalid(form)

    def form_valid(self, form):
        form = super().form_valid(form)
        link = 'https://copygram.com/register-confirm'
        send_reset_email(self.object, link)
        messages.info(self.request, 'Check email and confirm user.')
        return form
    
    def get_success_url(self):
        return reverse_lazy('users:password_reset_done')


class RegisterConfirmView(TemplateView):
    template_name = 'users/register_confirm.html'

    def get(self, request, **kwargs):
        uidb64 = kwargs['uidb64']
        token = kwargs['token']
        try:
            user, is_valid = check_token(uidb64, token)
            if not is_valid:
                messages.error(request, 'Token is invalid')
            else:
                user.is_active = True
                user.save()
                PeriodicTask.objects.get(name=f'delete-user-{user.id}').delete()
                messages.success(request, 'User has been created')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            messages.error(request, str(e))
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class AdminRegisterView(RegisterView):
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return response


class LoginUserView(LoginView):
    template_name = 'users/login.html'

    # If user has been alredy logged in, then prohibit login view.
    test = user_passes_test(
        # if
        test_func=lambda u: not u.is_authenticated,
        # else
        login_url=reverse_lazy('blogs:posts'),
    )
    @method_decorator(test)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        user = self.request.user
        if user.is_staff and user.is_superuser:
            return reverse_lazy('admin:index')
        return super().get_success_url()


class SetupTwoFaView(SetupView):
    """Setup two factor authentication."""

    template_name = 'users/enable_fa.html'

    def get_success_url(self):
        return reverse_lazy('users:edit_profile')


class DisableTwoFaView(DisableView):
    """Disable two factor authentication."""

    template_name = 'users/disable_fa.html'

    def get_success_url(self):
        return reverse_lazy('users:edit_profile')


class PasswordResetView(FormView):
    template_name = 'users/password_reset.html'
    success_url = reverse_lazy('users:password_user_confirm')
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        self.request.session['email'] = form.cleaned_data['email']
        return super().form_valid(form)


class PasswordUserConfirmView(TemplateView):
    template_name = 'users/password_user_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.request.session.get('email')
        user = User.objects.get(email=email)
        context['user_'] = user
        return context

    def post(self, request, *args, **kwargs):
        response = request.POST.get('confirm')
        email = request.session.pop('email')
        if response == 'yes':
            user = User.objects.get(email=email)
            link = 'https://copygram.com/password-reset'
            send_reset_email(user, link)
            messages.info(
                request,
                'Check email for the instructions to reset your password.',
            )
            return redirect('users:password_reset_done')
        else:
            return redirect('users:password_reset')
