

from .models import AccountType
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()

class AccountRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    type = forms.ChoiceField(
        choices=AccountType.choices,
        initial=AccountType.student
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name','last_name', 'email']



class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


# class UserEditForm(forms.ModelForm):
#     class Meta:
#         model = get_user_model()
#         fields = ['first_name', 'last_name', 'email']

#     def clean_email(self):
#         data = self.cleaned_data['email']
#         qs = User.objects.exclude(
#         id=self.instance.id
#         ).filter(
#         email=data
#         )
#         if qs.exists():
#             raise forms.ValidationError('Email already in use.')
#         return data

# class ProfileEditForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ['date_of_birth', 'photo']