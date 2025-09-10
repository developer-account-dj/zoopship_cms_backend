from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import (
    Page, FAQ, BlogPost, Banner, HowItWorks,PageSection,
    Impression, Feature, ContactInfo, Slide, SliderBanner,Section,SectionType
)
User = get_user_model()
from django.db.models import F,Max
from django.db import transaction

class PageMiniSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "slug", "is_active"]

    def get_is_active(self, page):
        """Return is_active from PageSection mapping"""
        section = self.context.get("section")
        if not section:
            return None
        mapping = PageSection.objects.filter(page=page, section=section).first()
        return mapping.is_active if mapping else None
import base64
from django.core.files.storage import default_storage
from drf_extra_fields.fields import Base64ImageField
import re
from django.core.files.base import ContentFile
class SectionSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()
    page_id = serializers.SerializerMethodField()
    page_slug = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()  # per-page order

    class Meta:
        model = Section
        fields = [
            "id",
            "slug",
            "title",
            "section_type",
            "data",
            # dynamic fields
            "pages",      # when multiple pages
            "page_id",    # only if filtering by single page
            "page_slug",  # only if filtering by single page
            "is_active",  # only if filtering by single page
            "order",      # per-page order
        ]

    def get_pages(self, obj):
        request = self.context.get("request")
        if not request:
            return []

        page_id = request.query_params.get("page_id")
        page_slug = request.query_params.get("page_slug")

        # ✅ If filtering by single page → don’t return pages[]
        if page_id or page_slug:
            return None  

        # ✅ Otherwise return all related pages with is_active
        pages = obj.pages.all()
        data = []
        for page in pages:
            mapping = PageSection.objects.filter(page=page, section=obj).first()
            data.append({
                "id": page.id,
                "slug": page.slug,
                "is_active": mapping.is_active if mapping else None,
                "order": mapping.order if mapping else None
            })
        return data

    def get_page_id(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        page_id = request.query_params.get("page_id")
        page_slug = request.query_params.get("page_slug")
    
        if not (page_id or page_slug):
            return None
    
        qs = obj.pagesection_set.all()
        if page_id:
            qs = qs.filter(page__id=page_id)
        elif page_slug:
            qs = qs.filter(page__slug=page_slug)
    
        mapping = qs.first()
        return mapping.page.id if mapping else None
    
    def get_page_slug(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        page_id = request.query_params.get("page_id")
        page_slug = request.query_params.get("page_slug")
    
        if not (page_id or page_slug):
            return None
    
        qs = obj.pagesection_set.all()
        if page_id:
            qs = qs.filter(page__id=page_id)
        elif page_slug:
            qs = qs.filter(page__slug=page_slug)
    
        mapping = qs.first()
        return mapping.page.slug if mapping else None
    def get_is_active(self, obj):
        request = self.context.get("request")
        if not request:
            return None

        page_id = request.query_params.get("page_id")
        page_slug = request.query_params.get("page_slug")

        if not (page_id or page_slug):
            return None

        qs = obj.pagesection_set.all()
        if page_id:
            qs = qs.filter(page__id=page_id)
        elif page_slug:
            qs = qs.filter(page__slug=page_slug)

        mapping = qs.first()
        return mapping.is_active if mapping else None
    
    def get_order(self, obj):
        """Return per-page order from PageSection"""
        request = self.context.get("request")
        if not request:
            return None
        page_id = request.query_params.get("page_id")
        page_slug = request.query_params.get("page_slug")
        if not (page_id or page_slug):
            return None

        qs = obj.pagesection_set.all()
        if page_id:
            qs = qs.filter(page__id=page_id)
        elif page_slug:
            qs = qs.filter(page__slug=page_slug)

        mapping = qs.first()
        return mapping.order if mapping else None

    def validate_data(self, value):
        """Handle Base64 images in 'data' dict, including handling dynamic image keys and nested structures."""
    
        def handle_images(data):
            if isinstance(data, list):
                for item in data:
                    handle_images(item)  # Recursively handle list items
            elif isinstance(data, dict):
                for key, file_data in data.items():
                    if isinstance(file_data, str) and file_data.startswith("data:image"):
                        # Detect MIME type
                        match = re.match(r"^data:(image/[\w\+\-\.]+);base64,", file_data)
                        if not match:
                            continue
    
                        mime_type = match.group(1)
    
                        if mime_type == "image/svg+xml":
                            # Handle SVG manually (store as raw XML)
                            format, imgstr = file_data.split(";base64,", 1)
                            ext = "svg"
                            file = ContentFile(base64.b64decode(imgstr), name=f"{key}.{ext}")
                            file_path = default_storage.save(f"sections/{file.name}", file)
                            data[key] = default_storage.url(file_path)
                        else:
                            # Handle raster images (JPG, PNG, GIF, HEIC, etc.)
                            base64_field = Base64ImageField()
                            file_obj = base64_field.to_internal_value(file_data)
                            file_path = default_storage.save(f"sections/{file_obj.name}", file_obj)
                            data[key] = default_storage.url(file_path)
                    else:
                        handle_images(file_data)
    
        handle_images(value)
        return value

    def to_representation(self, instance):
        """Serialize data, fixing media URLs in 'data' and cleaning fields based on request filters."""
        rep = super().to_representation(instance)
        request = self.context.get("request")
    
        # ✅ Fix media URLs inside `data`
        data = rep.get("data", {})
    
        def handle_media_urls(data):
            if isinstance(data, list):
                for item in data:
                    handle_media_urls(item)
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith("/media/") and request:
                        data[key] = request.build_absolute_uri(value)
                    else:
                        handle_media_urls(value)
    
        handle_media_urls(data)
        rep["data"] = data
    
        # ✅ Clean up depending on query params
        if request:
            page_id = request.query_params.get("page_id")
            page_slug = request.query_params.get("page_slug")
    
            if page_id or page_slug:
                # single page → remove pages[]
                rep.pop("pages", None)
            else:
                # multiple pages → remove flat fields
                rep.pop("page_id", None)
                rep.pop("page_slug", None)
                rep.pop("section_is_active", None)
        
        # Conditionally remove 'is_active' if its value is None
        if rep.get("is_active") is None:
            rep.pop("is_active")
    
        return rep



# ==========================
# THROUGH MODEL SERIALIZER
# ==========================
class PageSectionSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),
        source="section",
        write_only=True
    )

    class Meta:
        model = PageSection
        fields = ["section_id", "section", "is_active", "order"]

class PageSectionSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),
        source="section",
        write_only=True
    )

    class Meta:
        model = PageSection
        fields = ["section_id", "section", "is_active", "order"]

    def update(self, instance, validated_data):
        """
        PATCH update with automatic reordering.
        """
        new_order = validated_data.get("order", None)
        is_active = validated_data.get("is_active", instance.is_active)

        with transaction.atomic():
            if new_order is not None and new_order != instance.order:
                old_order = instance.order or 0

                if old_order < new_order:
                    # moving down → shift others up
                    PageSection.objects.filter(
                        page=instance.page,
                        order__gt=old_order,
                        order__lte=new_order
                    ).exclude(pk=instance.pk).update(order=F("order") - 1)
                else:
                    # moving up → shift others down
                    PageSection.objects.filter(
                        page=instance.page,
                        order__lt=old_order,
                        order__gte=new_order
                    ).exclude(pk=instance.pk).update(order=F("order") + 1)

                instance.order = new_order

            # update other fields
            instance.is_active = is_active
            instance.save(update_fields=["order", "is_active"] if new_order is not None else ["is_active"])

        return instance


class PageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

    children = serializers.SerializerMethodField()
    parent_title = serializers.CharField(source="parent.title", read_only=True)

    # 🔁 Instead of raw section IDs, we handle through model
    sections = PageSectionSerializer(source="pagesection_set", many=True, required=False)

    # Accept list of page types
    page_type = serializers.ListField(
        child=serializers.CharField(max_length=120),
        allow_empty=True,
        required=False ,
        allow_null=True    # 👈 this is the missing piece
    )

    class Meta:
        model = Page
        fields = [
            "id",
            "name",
            "title",
            "slug",
            "content",
            "is_active",      # page’s own active status
            "order",
            "parent_id",
            "parent_title",
            "page_type",
            "children",
            "sections",       # now includes section_is_active per-page
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "slug",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def get_children(self, obj):
        children = obj.children.all().order_by("order")
        return PageSerializer(children, many=True, context=self.context).data

    def create(self, validated_data):
        sections_data = validated_data.pop("pagesection_set", [])
        page = super().create(validated_data)
        for sec in sections_data:
            PageSection.objects.create(
                page=page,
                section=sec["section"],
                is_active=sec.get("is_active", True),
            )
        return page

    def update(self, instance, validated_data):
        sections_data = validated_data.pop("pagesection_set", None)
        page = super().update(instance, validated_data)
        if sections_data is not None:
            PageSection.objects.filter(page=page).delete()
            for sec in sections_data:
                PageSection.objects.create(
                    page=page,
                    section=sec["section"],
                    is_active=sec.get("is_active", True),
                )
        return page

# ==========================
# NAVIGATION SERIALIZER
# ==========================

class NavigationSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "title", "slug", "children", "order", "created_at"]

    def get_children(self, obj):
        # Only include active children ordered by `order`
        children = obj.children.filter(is_active=True).order_by("created_at")
        return NavigationSerializer(children, many=True).data
    



class SectionListSerializer(serializers.Serializer):
    sections = SectionSerializer(many=True)
    page_id = serializers.CharField(required=False)
    page_slug = serializers.CharField(required=False)

    def create(self, validated_data):
        sections_data = validated_data.pop("sections", [])
        page_id = validated_data.get("page_id")
        page_slug = validated_data.get("page_slug")

        # 🔹 find target page
        page = None
        if page_id:
            page = Page.objects.filter(id=page_id).first()
        elif page_slug:
            page = Page.objects.filter(slug=page_slug).first()

        created_sections = []
        mappings = []

        for section_data in sections_data:
            # extract extra fields
            is_active = section_data.pop("is_active", True)
            order = section_data.pop("order", None)

            # create section
            section = Section.objects.create(**section_data)

            mapping = None
            if page:
                with transaction.atomic():
                    # if no order → assign next available
                    if order is None:
                        max_order = PageSection.objects.filter(page=page).aggregate(
                            max_order=Max("order")
                        )["max_order"] or 0
                        order = max_order + 1
                    else:
                        # shift all >= order down by 1 to avoid duplicates
                        PageSection.objects.filter(page=page, order__gte=order).update(order=F("order") + 1)

                    mapping = PageSection.objects.create(
                        page=page,
                        section=section,
                        is_active=is_active,
                        order=order
                    )

                    # normalize orders sequentially
                    sections_on_page = PageSection.objects.filter(page=page).order_by("order")
                    for idx, ps in enumerate(sections_on_page, start=1):
                        if ps.order != idx:
                            PageSection.objects.filter(pk=ps.pk).update(order=idx)

            created_sections.append(section)
            mappings.append(mapping)

        return {
            "sections": created_sections,
            "page": page,
            "mappings": mappings,
        }

# ==========================
# CONTENT SERIALIZERS
# ==========================
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"

class BlogPostSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = BlogPost
        fields = "__all__"

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"

class HowItWorksSerializer(serializers.ModelSerializer):
    class Meta:
        model = HowItWorks
        fields = "__all__"

class ImpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impression
        fields = "__all__"

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"

class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['id', 'contact_type', 'label', 'value', 'icon', 'order', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class SlideSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Slide
        fields = ["id", "heading", "description", "image"]

class SliderBannerSerializer(serializers.ModelSerializer):
    slides = SlideSerializer(many=True, required=False)

    class Meta:
        model = SliderBanner
        fields = ["id", "title", "slug", "is_active", "slides"]

    def create(self, validated_data):
        slides_data = validated_data.pop("slides", [])
        slider = SliderBanner.objects.create(**validated_data)
        for slide_data in slides_data:
            Slide.objects.create(slider=slider, **slide_data)
        return slider

    def update(self, instance, validated_data):
        slides_data = validated_data.pop("slides", None)
        instance.title = validated_data.get("title", instance.title)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save()

        if slides_data is not None:
            for slide_data in slides_data:
                if "id" in slide_data:
                    slide = Slide.objects.get(id=slide_data["id"], slider=instance)
                    for attr, value in slide_data.items():
                        setattr(slide, attr, value)
                    slide.save()
                else:
                    Slide.objects.create(slider=instance, **slide_data)
        return instance





class SectionOrderSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="section.id")
    slug = serializers.CharField(source="section.slug")
    title = serializers.CharField(source="section.title")
    section_type = serializers.CharField(source="section.section_type")

    page_id = serializers.CharField(source="page.id")
    page_slug = serializers.CharField(source="page.slug")
    is_active = serializers.BooleanField()
    order = serializers.IntegerField()

    class Meta:
        model = PageSection
        fields = [
            "id",
            "slug",
            "title",
            "section_type",
            "page_id",
            "page_slug",
            "is_active",
            "order",
        ]
    def get_mapping(self, obj):
        """Helper to get PageSection mapping"""
        request = self.context.get("request")
        page_id = request.query_params.get("page_id") if request else None
        page_slug = request.query_params.get("page_slug") if request else None

        qs = obj.pagesection_set.all()
        if page_id:
            qs = qs.filter(page__id=page_id)
        elif page_slug:
            qs = qs.filter(page__slug=page_slug)
        return qs.first()

    def get_page_id(self, obj):
        mapping = self.get_mapping(obj)
        return mapping.page.id if mapping else None

    def get_page_slug(self, obj):
        mapping = self.get_mapping(obj)
        return mapping.page.slug if mapping else None

    def get_is_active(self, obj):
        mapping = self.get_mapping(obj)
        return mapping.is_active if mapping else None

    def get_order(self, obj):
        mapping = self.get_mapping(obj)
        return mapping.order if mapping else None