from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfileInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user')
    location = models.CharField(max_length=20, blank=True)
    age = models.IntegerField(blank=True, default=13)
    friend = models.ManyToManyField(User, blank=True, related_name='friend')
    num_friends = models.IntegerField(default=0)
    profile_pic_url = models.URLField(default="https://avatars.dicebear.com/api/bottts/ssaa.svg")

    def __str__(self):
        return self.user.username

class Friend(models.Model):
    source = models.ForeignKey(UserProfileInfo, on_delete=models.CASCADE, blank=False, related_name="source")
    destination = models.ForeignKey(UserProfileInfo, on_delete=models.CASCADE, blank=False, related_name="destination")