from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from core.models import BaseModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import random
User = get_user_model()


# -------------------------
# Page Model
# -------------------------

class Page(BaseModel):
    name = models.CharField(max_length=255, default="name")
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # navigation fields
    parent_id = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)

    # sections through PageSection
    sections = models.ManyToManyField(
        "Section",
        through="PageSection",
        related_name="pages",
        blank=True
    )

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return f"{self.id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title or self.name)
            slug = base_slug
            count = 1
            while Page.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)



# -------------------------
# Section Model
# -------------------------

class Section(BaseModel):
    title = models.CharField(max_length=255, default="section",unique=True)
    slug = models.SlugField(blank=True, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            count = 1
            while Section.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# -------------------------
# SectionItem (Generic)
# -------------------------
class SectionItem(BaseModel):
    section = models.ForeignKey("Section", related_name="items", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = ("section", "content_type", "object_id")

    def __str__(self):
        return f"{self.section.title} → {self.content_type} ({self.object_id})"

# -------------------------
# PageSection (Ordering)
# -------------------------
class PageSection(BaseModel):
    id = models.CharField(
        max_length=8,
        unique=True,
        editable=False,
        primary_key=True
    )
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="page_sections")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="section_pages")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("page", "section")

    def __str__(self):
        return f"{self.page.title} - {self.section.title} ({self.order})"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_custom_id()
        super().save(*args, **kwargs)

    def generate_custom_id(self):
        prefix = "PGSE"
        suffix = f"{random.randint(0, 9999):04d}"
        return prefix + suffix


# -------------------------
# Section Data Models
# -------------------------

class FAQ(BaseModel):
    question = models.CharField(max_length=500, unique=True)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.id} - {self.question}"


class BlogPost(BaseModel):
    # author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    summary = models.TextField()
    content = models.TextField()
    is_active = models.BooleanField(default=False)

    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            count = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug

        if not self.meta_title:
            self.meta_title = self.title
        if not self.meta_description:
            self.meta_description = self.summary[:160]
        if not self.meta_keywords:
            self.meta_keywords = ", ".join(self.title.lower().split())

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.title}"


class Banner(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    heading = models.CharField(max_length=255)
    subheading = models.CharField(max_length=500, blank=True, null=True, default="zoopship")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="banners/")
    url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    extra_fields = models.JSONField(blank=True, null=True, default=dict)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Banner.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.title}"


class ContactInfo(BaseModel):
    CONTACT_TYPE_CHOICES = [
        ("email", "Email"),
        ("phone", "Phone"),
        ("address", "Address"),
    ]
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=200)
    icon = models.ImageField(upload_to="icon/")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["contact_type", "order"]
        verbose_name_plural = "Contact Information"

    def __str__(self):
        return f"{self.id} - {self.label}: {self.value}"


class HowItWorks(BaseModel):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    steps = models.JSONField(blank=True, null=True, default=list)
    background_image = models.ImageField(upload_to="how_it_works/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    extra_fields = models.JSONField(blank=True, null=True, default=dict)

    def __str__(self):
        return f"{self.id} - {self.title}"


class Impression(BaseModel):
    TYPE_CHOICES = (
        ("goal", "Goal"),
        ("vision", "Vision"),
        ("mission", "Mission"),
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to="goal_vision_mission/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "impression"
        verbose_name_plural = "impressions"

    def __str__(self):
        return f"{self.id} - {self.get_type_display()} - {self.title}"


class Feature(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to="features/icons/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.id} - {self.title}"


class SliderBanner(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            counter = 1
            while SliderBanner.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Slide(BaseModel):
    slider = models.ForeignKey(SliderBanner, related_name="slides", on_delete=models.CASCADE)
    heading = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="slider_banners/")