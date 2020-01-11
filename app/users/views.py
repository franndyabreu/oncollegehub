from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
# from django.contrib.auth.models import User
from .models import Student
from blog.views import get_college_ranking, get_student_ranking
from django.db import connection
from django.views.generic import (
    DetailView,
    CreateView,
    UpdateView,
    ListView,
)


class UserRegistration(CreateView):
    model = Student
    form_class = UserRegisterForm

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('blog-home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['registration_form'] = UserRegisterForm()
        get_college_ranking(context)
        get_student_ranking(context)
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')

        else:
            messages.error(request, "There are some errors with your registration, please check below: ")

        return render(request, 'users/register.html', {'registration_form': form})


@method_decorator(login_required, name='dispatch')
class UserProfile(DetailView):
    model = Student
    context_object_name = 'user_object'

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        user_following = self.request.user.profile

        if request.POST.get('follow'):
            user.profile.follower.add(user_following)
            user_following.following.add(user.profile)
            user_following.save()
            user.save()

        elif request.POST.get('unfollow'):
            user.profile.follower.remove(user_following)
            user_following.following.remove(user.profile)
            user.save()
            user_following.save()

        return HttpResponseRedirect(user.profile.get_absolute_url())

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        following = self.get_object().profile.following.all()
        followers = self.get_object().profile.follower.all()
        context['following'] = following
        context['followers'] = followers
        get_college_ranking(context)
        get_student_ranking(context)
        return context


class UserUpdateProfile(UserPassesTestMixin, UpdateView):
    model = Student
    user_details_form = UserUpdateForm
    context_object_name = 'user_object'
    fields = ['first_name', 'last_name']
    success_url = '/'

    def post(self, request, *args, **kwargs):
        # Call the parent before overriding to save the UserUpdateForm and the ProfileUpdate
        super().post(self, request, *args, **kwargs)
        p_form = ProfileUpdateForm(self.request.POST, self.request.FILES, instance=self.request.user.profile)
        if p_form.is_valid():
            p_form.save()
            return redirect(f"/users/{self.kwargs.get('pk')}/{self.kwargs.get('username')}")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        p_form = ProfileUpdateForm(instance=self.request.user.profile)
        data['relevant_post'] = None
        data['p_form'] = p_form
        get_college_ranking(data)
        get_student_ranking(data)
        return data

    def test_func(self):
        user = self.get_object()
        return False if self.request.user != user else True


class UserDetailView(DetailView):
    model = Student
    template_name = 'users/user_detail.html'


class UserProfileFollowing(ListView):
    model = Student
    template_name = 'users/users_following.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = Student.objects.filter(id=self.kwargs['pk']).first()
        following = user.profile.following.all()
        context['following_list'] = following
        get_college_ranking(context)
        get_student_ranking(context)
        return context


class UserProfileFollowers(ListView):
    model = Student
    template_name = 'users/user_followers.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = Student.objects.filter(id=self.kwargs['pk']).first()
        followers = user.profile.follower.all()
        context['followers_list'] = followers
        get_college_ranking(context)
        get_student_ranking(context)
        return context
