from typing import Iterable
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class AccountType(models.TextChoices):
    student = 'Student'
    teacher = 'Teacher'

class Profile(models.Model):
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='profile'
    )
    photo = models.ImageField(
    upload_to='accounts/profiles/%Y/%m/%d/',
    blank=True
    )
    type = models.CharField(
    max_length=20,
    choices=AccountType.choices,
    default=AccountType.student
    )


    def save(self,*args,**kwargs):
        instructors_group = Group.objects.get(name='Instructors')
        if self.type == AccountType.teacher:
            instructors_group.user_set.add(self.user)
        else:
            instructors_group.user_set.remove(self.user)
        return super(Profile,self).save(*args,**kwargs)
    
    def __str__(self):
        return f'Profile of {self.user.username}'
    
