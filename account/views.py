from typing import Any
from django.contrib.auth import authenticate, get_user_model, login
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import logout
from .forms import LoginForm , AccountRegistrationForm 
from django.contrib.auth.decorators import login_required
from .models import Profile,AccountType
from django.contrib import messages
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin 



User = get_user_model()

class RegisterView(View):
    def post(self, request):        
        form = AccountRegistrationForm(request.POST)
        if form.is_valid():
            # Create a new user object but avoid saving it yet
            user = form.save()
            # Create the user profile
            Profile.objects.create(
                user=user,
                type=request.POST.get('type'),
                photo=request.POST.get('photo')
                )
            
            return render(
            request,
            'account/register_done.html',
            {'new_user': user}
            )
        else:
            return render(
            request,
            'account/register.html',
            {'form': form}
            )
        
    def get(self, request):
        form = AccountRegistrationForm()
        return render(
        request,
        'account/register.html',
        {'form': form}
        )
            

class LoginView(View):

    def post(self, request):
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                user = authenticate(
                request,
                username=cd['username'],
                password=cd['password']
                )
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        if user.profile.type == AccountType.teacher:
                            return redirect('home')
                        return redirect('home')
            return render(request, 'registration/login.html', {'form': form})
                
        else:
            form = LoginForm()
        return render(request, 'registration/login.html', {'form': form})
    
    def get(self, request):
        form = LoginForm()
        return render(request, 'registration/login.html', {'form': form})


class LogoutView(LoginRequiredMixin,View):
    def get(self, request):
        logout(request)
        return redirect('home')

class ProfileDetailView(LoginRequiredMixin,DetailView):
    model = User
    template_name = 'account/profile.html'
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if  request.user != self.get_object():
            return redirect('profile_detail' , request.user.id)
        return super().get(request, *args, **kwargs)


class ProfileUpdateDeleteView(LoginRequiredMixin,UpdateView):
    model = User
    template_name = 'account/profile.html'
    form_class = AccountRegistrationForm
    def get_form(self, form_class: BaseModelForm | None = ...) -> BaseModelForm:
        if self.request.user != self.get_object():
            print(self.get_object().id)
            return redirect('profile_detail' , self.request.user.id)
        form = AccountRegistrationForm(instance=self.get_object())
        form.fields.pop('password1')
        form.fields.pop('password2')
        return form
    
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        user = User.objects.get(id=request.user.id)
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.profile.type = request.POST.get('type')
        user.profile.photo = request.POST.get('photo')
        user.save()
        return redirect('profile_detail', request.user.id)
        
