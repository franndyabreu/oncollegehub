from django.shortcuts import render, redirect
from .models import Question, Answer, Voter, College
from users.models import Student
from .forms import CommentForm, PostForm
from django.db.models import Count
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView, )


def get_college_ranking(context):
    college_ranking = College.objects.annotate(question_count=Count('question')) \
        .order_by('-question_count')
    try:
        context['college_ranking'] = college_ranking[0:4]
    finally:
        return context


def get_student_ranking(context):
    student_ranking = Student.objects.annotate(answer_count=Count('answer')) \
        .order_by('-answer_count')
    try:
        context['student_ranking'] = student_ranking[0:4]
    finally:
        return context


class PostListView(ListView):
    model = Question
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-rating']
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        get_college_ranking(context)
        get_student_ranking(context)
        return context


class PostCollegeListView(ListView):
    model = Question
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['rating']
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        get_college_ranking(context)
        get_student_ranking(context)
        return context

    def get_queryset(self):
        print(Question.objects.filter(college_id=self.kwargs.get('pk', 1)).query)
        return Question.objects.filter(college_id=self.kwargs.get('pk', 1))


class SchoolsListView(ListView):
    model = College
    template_name = 'blog/schools.html'
    context_object_name = 'schools'
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        get_student_ranking(context)
        get_college_ranking(context)
        return context


class PostDetailView(FormMixin, LoginRequiredMixin, DetailView):
    model = Question
    form_class = CommentForm
    context_object_name = 'posts'
    template_name = 'blog/post_detail.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.get_object()
        form.instance.college = self.request.user.college
        form.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = Answer.objects.filter(question=self.get_object())
        get_college_ranking(context)
        get_student_ranking(context)
        return context

    def post(self, request, *args, **kwargs):
        question = self.get_object()
        user = self.request.user
        success_url = f"/post/{self.kwargs.get('pk')}/{self.kwargs.get('title')}"
        voter = Voter.objects.filter(user=user, Question=question)
        print(voter.query)

        # Comment Button
        if self.request.POST.get('add_comment'):
            form = self.form_class(request.POST)
            if form.is_valid():
                answer = Answer(question=self.get_object(), content=form.cleaned_data['content'],
                                author_id=self.request.user.id, college_id=self.request.user.college_id)
                answer.save()
                question.answer_set.add(answer)
                self.success_url = success_url
                return self.form_valid(form)

            else:
                messages.error(request, 'Please enter a valid Answer!')
                return redirect(success_url)

            # Like Button
        elif self.request.POST.get('like'):
            if voter.exists():
                question.rating -= 1
                voter.delete()
                question.save()
                return redirect(success_url)

            elif question.author == user:
                messages.info(request, 'You cannot rate your own posts!')
                return redirect(success_url)

            else:
                voter = Voter(user=user, Question=question)
                question.rating += 1
                question.save()
                voter.save()
                return redirect(success_url)

        elif self.request.POST.get('question_solved'):
            if self.request.user.id == question.author.id:
                if question.is_answered:
                    messages.error(request, 'Question already solved!')
                    return redirect(success_url)

                else:
                    question.is_answered = True
                    answer = Answer.objects.filter(id=self.kwargs['fk']).first()
                    answer.is_approved = True
                    answer.save()
                    question.save()
                    return redirect(success_url)
            else:
                return HttpResponse('FORBIDDEN')
        else:
            messages.error(request, 'INVALID POST REQUEST')
            return redirect('blog-home')


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.college = self.request.user.college
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_college_ranking(context)
        get_student_ranking(context)
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Question
    fields = ['title', 'content']
    template_name = 'blog/post_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_college_ranking(context)
        get_student_ranking(context)
        return context

    def form_valid(self, form):
        form.instance.author = self.get_object().author
        form.instance.college = self.get_object().author.college
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return True if self.request.user == post.author or \
                       self.request.user.is_superuser else False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Question
    success_url = '/'
    template_name = 'blog/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        return True if self.request.user == post.author or self.request.user.is_superuser else False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_student_ranking(context)
        get_college_ranking(context)
        return context


class CommentDeleteView(UserPassesTestMixin, DeleteView):
    model = Answer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_student_ranking(context)
        get_college_ranking(context)
        return context

    def test_func(self):
        """
            comment is the Author
        """
        answer = self.get_object()
        return True if self.request.user == answer.author or self.request.user.is_superuser else False

    def get_success_url(self):
        return reverse('post-detail', kwargs={'pk': self.get_object().question.pk, 'title': self.get_object()
                       .question.title})


class CommentUpdateView(UpdateView):
    model = Answer
    template_name = 'blog/comment_form.html'
    fields = ['content']

    def get_success_url(self):
        """
            Get a specific comment  to be updated,
            the primary key and the title will be taken off the Url.
        """
        return reverse('post-detail',
                       kwargs={'pk': self.get_object().question.pk,
                               'title': self.get_object().question.title})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_student_ranking(context)
        get_college_ranking(context)
        return context


class SearchListView(ListView):
    model = Question
    template_name = 'blog/search_results.html'

    def get(self, request, *args, **kwargs):
        """
        If the user isn't authenticated, the search result will be sorted by the rating of the posts.
        If the user is authenticated, the search result will be sorted by user's college.
        """
        search_query = request.GET.get('q', None)
        if search_query is not None:
            if self.request.user.is_authenticated:
                self.queryset = Question.objects.filter(
                    title__icontains=search_query).order_by('-rating')
            else:
                self.queryset = Question.objects.filter(title__icontains=search_query).order_by('-rating')
                if not self.queryset:
                    messages.error(request, f'No results found for {search_query}')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """
            Return a list of results based on the value input in the search bar,
            if the list if empty -> 'No result found' is returned.
        """
        context = super().get_context_data(**kwargs)
        context['list_result'] = self.queryset
        get_student_ranking(context)
        get_college_ranking(context)
        return context


def about(request):
    """
        FURTHER DEVELOPMENT
    """
    success = True
    return render(request, 'blog/about.html', {'success:': success})
