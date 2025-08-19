from django.db import models
from django.conf import settings
import random
import string

class BaseModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)
    id = models.CharField(
        max_length=8,
        unique=True,
        editable=False,
        primary_key=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            new_id = self.generate_custom_id()
            while self.__class__.objects.filter(id=new_id).exists():
                new_id = self.generate_custom_id()
            self.id = new_id
        super().save(*args, **kwargs)

    def generate_custom_id(self):
        # First 4 chars from model name (uppercase, padded/truncated to 4)
        prefix = self.__class__.__name__[:4].upper().ljust(4, 'X')
        # Last 4 chars: random digits
        suffix = f"{random.randint(0, 9999):04d}"
        return prefix + suffix