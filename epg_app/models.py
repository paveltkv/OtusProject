from django.db import models


class Epg(models.Model):
    name = models.CharField(max_length=64, unique=True)
    url = models.URLField(max_length=1024, blank=False, null=False)
    logos_url = models.URLField(max_length=1024, blank=True, null=True)
    download_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)
    error_message = models.CharField(max_length=128, blank=True, null=True)
    channels_num = models.IntegerField(blank=True, null=True)
    programme_num = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f'{self.name}'


class EpgItem(models.Model):
    epg = models.ForeignKey(Epg, on_delete=models.CASCADE)
    tvg_id = models.CharField(max_length=64)

    class Meta:
        unique_together = ('epg', 'id',)

    def __str__(self):
        return f'{self.pk}'


class EpgChannel(models.Model):
    epg_item = models.ForeignKey(EpgItem, on_delete=models.CASCADE, related_name='channels')
    tvg_name = models.CharField(max_length=128)
    tvg_name_synonyms = models.JSONField(blank=True)
    icon_url = models.URLField(max_length=1024, blank=True)

    def __str__(self):
        return f'{self.tvg_name}'


class EpgProgramme(models.Model):
    epg_item = models.ForeignKey(EpgItem, on_delete=models.CASCADE, related_name='programmes')
    start = models.DateTimeField()
    stop = models.DateTimeField()
    data = models.TextField(blank=True)

    class Meta:
        unique_together = ('epg_item', 'start',)

    def __str__(self):
        return f'{self.start, self.data}'
