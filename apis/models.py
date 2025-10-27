# jdgen/models.py
from django.db import models
from django.contrib.postgres.fields import JSONField  # or models.JSONField for Django 3.1+

class JDRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    input_json = models.JSONField()            # dynamic input saved
    word_count = models.IntegerField(null=True, blank=True)
    tone = models.CharField(max_length=64, blank=True, default="")
    language = models.CharField(max_length=32, blank=True, default="English")
    output_text = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=32, default="pending")  # pending/complete/failed
    error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"JDRequest #{self.id} ({self.status})"

class TotalUsage(models.Model):
    request_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Total Usage: {self.request_count} requests"