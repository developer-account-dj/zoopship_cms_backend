from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from core.models import BaseModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import random
User = get_user_model()
from django.db import transaction
from django.db.models import F,Max
# -------------------------
# Page Model
# -------------------------

class Page(BaseModel):
    name = models.CharField(max_length=255, default="name")
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    page_type = models.JSONField(default=list, blank=True,null=True)

    # navigation fields
    parent_id = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )
    order = models.PositiveIntegerField(default=0)


    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return f"{self.id} - {self.title}"


    def save(self, *args, **kwargs):
        # Special case: Home page slug should always be "/"
        if self.title.lower() == "home":
            self.slug = "/"
        elif not self.slug or self.slug.strip() == "":
            # Auto-generate slug for all other pages
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
class PageSection(models.Model):
    page = models.ForeignKey("Page", on_delete=models.CASCADE)
    section = models.ForeignKey("Section", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(null=True, blank=True)   # 👈 allow null for auto-assign

    class Meta:
        unique_together = ("page", "section")
        ordering = ["order"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # CREATE
            if not self.pk:
                if self.order is None:
                    # assign next available
                    max_order = PageSection.objects.filter(page=self.page).aggregate(
                        max_order=Max("order")
                    )["max_order"] or 0
                    self.order = max_order + 1
                else:
                    # shift all >= new order down
                    PageSection.objects.filter(page=self.page, order__gte=self.order).update(order=F("order") + 1)

            # UPDATE
            else:
                old_order = PageSection.objects.filter(pk=self.pk).values_list("order", flat=True).first()
                if old_order != self.order:
                    # shift other sections
                    if old_order < self.order:
                        PageSection.objects.filter(
                            page=self.page,
                            order__gt=old_order,
                            order__lte=self.order
                        ).exclude(pk=self.pk).update(order=F("order") - 1)
                    else:
                        PageSection.objects.filter(
                            page=self.page,
                            order__lt=old_order,
                            order__gte=self.order
                        ).exclude(pk=self.pk).update(order=F("order") + 1)

            super().save(*args, **kwargs)

            # normalize all orders to be sequential
            sections = PageSection.objects.filter(page=self.page).order_by("order")
            for idx, ps in enumerate(sections, start=1):
                if ps.order != idx:
                    PageSection.objects.filter(pk=ps.pk).update(order=idx)


class Section(BaseModel):
    pages = models.ManyToManyField(
        Page,
        through="PageSection",   # 👈 custom through model
        related_name="sections",
        blank=True
    )
    data = models.JSONField(default=dict, help_text="Dynamic data for this section")

    section_type = models.CharField(max_length=120, default="sectiontype")

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.section_type}"
    
    def save(self, *args, **kwargs):
        # Generate slug from title if empty
        if not self.slug or self.slug.strip() == "":
            base_slug = slugify(self.title)
            slug = base_slug
            count = 1
            while Section.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)


class SectionType(BaseModel):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the section type (e.g. Banner, About)")
    description = models.TextField(blank=True, null=True)
    schema = models.JSONField(
        default=dict,
        help_text="(Optional) Define expected fields for this section, e.g. {title: string, image: url}"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = ("Section Type")
        verbose_name_plural = ("Section Types")

    def _str_(self):
        return self.name
    

    


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
    title = models.CharField(max_length=255)
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
    title = models.CharField(max_length=255,)
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