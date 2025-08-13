from django.db import models
from core.models import BaseModel
from django.utils.text import slugify
class Page(BaseModel):
    name = models.CharField(max_length=255,default="name")
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate slug from title or name
            base_slug = slugify(self.title or self.name)
            slug = base_slug
            count = 1
            # Check for unique slug and increment count if needed
            while Page.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)




class FAQ(BaseModel):
    question = models.CharField(max_length=500, unique=True)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)  # for sorting FAQs
    
    def __str__(self):
        return self.question
    


from django.contrib.auth import get_user_model
from core.models import BaseModel
User = get_user_model()

class BlogPost(BaseModel):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    summary = models.TextField()
    content = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            count = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    

class Banner(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='banners/')
    url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    def __str__(self):
        return self.title



class NavigationItem(BaseModel):
    title = models.CharField(max_length=100,unique=True)
    url = models.CharField(max_length=255, blank=True, null=True)  # URL or route
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title