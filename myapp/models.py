from django.db import models
import uuid

# Create your models here.

class ChatSession(models.Model):
    id = models.CharField(max_length=100, primary_key=True, default=uuid.uuid4)
    user_id = models.CharField(max_length=100, db_index=True)  # Store user ID from the custom auth system
    title = models.CharField(max_length=200, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20) # 'user' or 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
