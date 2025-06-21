from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = CKEditor5Field()
    author = models.CharField(max_length=100)
    published = models.BooleanField(default=False)
    published_date = models.DateTimeField(blank=True, null=True)
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title
