from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, College, Student


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    college = forms.ModelChoiceField(queryset=College.objects.all())

    class Meta:
        model = Student
        exclude = ('first_name', 'last_name')
        fields = ['username', 'email', 'college',
                  'password1', 'password2']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Student
        fields = ['first_name', 'last_name']
