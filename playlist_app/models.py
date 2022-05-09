from django.db import models

# Create your models here.
from user_app.models import CustomUser


class PlayList(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, unique=True)
    url = models.URLField(max_length=1024, blank=False, null=False)
    marker = models.CharField(max_length=10)
    data = models.TextField(blank=True, null=True)
    download_time = models.DateTimeField(null=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.id, self.name, self.url}'


# class Channel(models.Model):
#     name = models.CharField(max_length=64, unique=True)
#     resolution = models.CharField(max_length=32)
#     desc = models.TextField(blank=True)
#
#     def __str__(self):
#         return f'{self.name} ({self.get_categories()})'
#
#     def get_categories(self):
#         categories_list = self.channelcategory_set.all()
#         return ', '.join(map(str, categories_list))
#
#
# class ChannelCategory(models.Model):
#     name = models.CharField(max_length=64, unique=True)
#     channel = models.ManyToManyField(Channel)
#
#     def __str__(self):
#         return f'{self.name}'
#
#     def get_channels(self):
#         channel_list = self.channel_set.all()
#         return ', '.join(map(str, channel_list))
