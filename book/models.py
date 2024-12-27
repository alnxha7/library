from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return self.title
    
class Borrow(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        book = models.ForeignKey(Book, on_delete=models.CASCADE)
        borrow_date = models.DateField()
        return_date = models.DateField(blank=True, null=True)
        returned = models.BooleanField(default=False)

