from django.db import models
from django.utils import timezone


class UserSettings(models.Model):
    """Stores per-user configuration (single row, pk=1 for anonymous apps)."""
    custom_prompt = models.TextField(blank=True, default='')
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Settings'

    def __str__(self):
        return f"UserSettings (updated {self.updated_at:%d %b %Y %H:%M})"

    @classmethod
    def get_solo(cls):
        """Always return the single settings row, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def to_dict(self):
        return {
            'custom_prompt': self.custom_prompt,
        }


class ChatSession(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    date_label = models.CharField(max_length=30, blank=True)
    concluded  = models.BooleanField(default=False)
    conclusion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.date_label:
            self.date_label = self.created_at.strftime('%d %b %Y')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session {self.pk} — {self.date_label}"

    def to_dict(self):
        return {
            'id':         self.pk,
            'date_label': self.date_label,
            'concluded':  self.concluded,
            'created_at': self.created_at.isoformat(),
        }


class Message(models.Model):
    ROLE_USER      = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_CHOICES   = [(ROLE_USER, 'User'), (ROLE_ASSISTANT, 'Assistant')]

    session   = models.ForeignKey(ChatSession, on_delete=models.CASCADE,
                                  related_name='messages')
    role      = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content   = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"

    def to_dict(self):
        return {
            'id':        self.pk,
            'role':      self.role,
            'content':   self.content,
            'timestamp': self.timestamp.isoformat(),
        }