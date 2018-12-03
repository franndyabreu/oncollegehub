from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
# from django.contrib.auth.models import User
from users.models import Student, College
from django.urls import reverse
from django.core import validators


class AbstractPostModel(models.Model):
    title = models.CharField(validators=[validators.MinLengthValidator(10)],
                             null=False, max_length=500)
    content = models.TextField(validators=[validators.MinLengthValidator(10)], null=False)
    post_date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(Student, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk, 'title': self.title})


class Question(AbstractPostModel):
    is_answered = models.BooleanField(default=False)


class Answer(AbstractPostModel):
    is_approved = models.BooleanField(default=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)


class Voter(models.Model):
    Question = models.ForeignKey(Question, on_delete=models.CASCADE)
    Answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(Student, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username + ' vote on post: ' + self.Question.title


class Comment(AbstractPostModel):
    Question = models.ForeignKey(Question, on_delete=models.CASCADE)
    author = models.ForeignKey(Student, on_delete=models.CASCADE)
    content = models.TextField(null=False)

    def __str__(self):
        return self.author.username + ' comment on post: ' + self.Question.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk, 'title': self.Question.title})
