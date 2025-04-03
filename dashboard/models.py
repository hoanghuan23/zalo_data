# ZaloMessage model definition

from django.db import models

class Message(models.Model):
    message_id = models.TextField(unique=True)
    sender_id = models.TextField()
    sender_name = models.TextField()
    message = models.TextField()
    timestamp = models.DateTimeField()
    attachments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'

    def __str__(self):
        return f"{self.sender_name}: {self.message[:50]}..."
