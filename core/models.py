
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class UserStampedModel(models.Model):
   created_by = models.ForeignKey(
      User, on_delete=models.CASCADE, null=True, blank=True,
      related_name='%(class)s_creator'
   )
   updated_by = models.ForeignKey(
      User, on_delete=models.CASCADE, null=True, blank=True,
      related_name='%(class)s_updater'
   )
   class Meta:
      abstract = True

class TimeStampedModel(models.Model):
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      abstract = True

class CoreSensorType(models.Model):
   name = models.CharField(max_length=255)
   description = models.TextField()

   def __str__(self):
      return self.name
