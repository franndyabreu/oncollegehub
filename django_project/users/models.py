from django.db import models
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from PIL import Image


class College(models.Model):
    name = models.CharField(null=False, max_length=50)
    address = models.CharField(null=False, max_length=50)

    def __str__(self):
        return self.name


class Student(AbstractUser):
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True)


class Profile(models.Model):
    user = models.OneToOneField(Student, on_delete=models.CASCADE)
    follower = models.ManyToManyField('self', symmetrical=False, related_name='followers')
    following = models.ManyToManyField('self', symmetrical=False, related_name='follows')
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, **kwargs):
        super().save()
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def get_absolute_url(self):
        return reverse('profile', kwargs={'pk': self.pk, 'username': self.user.username})


Student._meta.get_field('email')._unique = True
