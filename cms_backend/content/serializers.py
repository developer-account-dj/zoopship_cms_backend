from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import (
    Page, FAQ, BlogPost, Banner, HowItWorks,
    Impression, Feature, ContactInfo,
    Section, SectionItem, PageSection, Slide, SliderBanner
)
User = get_user_model()


# ==========================
# PAGE SERIALIZER
# ==========================

class PageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

    sections = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    parent_title = serializers.CharField(source="parent.title", read_only=True)

    class Meta:
        model = Page
        fields = [
            "id",
            "name",
            "title",
            "slug",
            "content",
            "is_active",
            "order",
            "parent_id",
            "parent_title",
            "sections",
            "children",
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

    def get_sections(self, obj):
        # ✅ return ALL sections (active + inactive)
        page_sections = PageSection.objects.filter(page=obj).order_by("order")
        return PageSectionSerializer(page_sections, many=True).data

    def get_children(self, obj):
        # ✅ return ALL children (active + inactive)
        children = obj.children.all().order_by("order")
        return PageSerializer(children, many=True).data


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

# ==========================
# DYNAMIC SECTION SERIALIZER
# ==========================


# ==========================
# HELPER: Parse flat form-data
# ==========================
# 

import re
from collections import defaultdict

def parse_items_from_request(request_data):
    """
    Parse nested keys like:
    items[0][slides][1][heading] -> 
    [{'slides': [{'heading': ...}, {...}]}]
    """
    items_dict = defaultdict(dict)

    for key, value in request_data.items():
        if not key.startswith("items["):
            continue

        # Split into parts: items[0][slides][1][heading] -> ['0', 'slides', '1', 'heading']
        parts = re.findall(r"\[(.*?)\]", key)
        if not parts:
            continue

        idx = int(parts[0])  # top-level item index
        current = items_dict[idx]

        cursor = current
        for i, p in enumerate(parts[1:]):
            is_last = (i == len(parts[1:]) - 1)

            # If it's an index → list
            if p.isdigit():
                p = int(p)
                if not isinstance(cursor, list):
                    # replace cursor with list if needed
                    new_list = []
                    if cursor == current:  # top level
                        # replace dict with list directly
                        items_dict[idx] = new_list
                        cursor = items_dict[idx]
                    else:
                        # find key in parent dict that points to cursor
                        for k, v in current.items():
                            if v is cursor:
                                current[k] = new_list
                                break
                        cursor = new_list

                while len(cursor) <= p:
                    cursor.append({})
                cursor = cursor[p]

            else:  # normal key → dict
                if is_last:
                    cursor[p] = value
                else:
                    if p not in cursor:
                        cursor[p] = {}
                    cursor = cursor[p]

    # Convert dict to sorted list
    return [items_dict[k] for k in sorted(items_dict.keys())]



CONTENT_SERIALIZER_MAP = {
    "faq": FAQSerializer,
    "blogpost": BlogPostSerializer,
    "banner": BannerSerializer,
    "howitworks": HowItWorksSerializer,
    "impression": ImpressionSerializer,
    "feature": FeatureSerializer,
    "contactinfo": ContactInfoSerializer,
    "sliderbanner": SliderBannerSerializer,
}


URL_TO_CONTENT_TYPE = {
    "slider-banner": "sliderbanner",
    "blog-post": "blogpost",
    "faq": "faq",
    "banner": "banner",
    "how-it-works": "howitworks",
    "impression": "impression",
    "feature": "feature",
    "contact-info": "contactinfo",
}

# ==========================
# SECTION ITEM SERIALIZER
# ==========================



class SectionItemSerializer(serializers.ModelSerializer):
    object_id = serializers.CharField(read_only=True)
    content_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SectionItem
        fields = ["id", "object_id", "content_object"]

    def get_content_object(self, instance):
        model_name = instance.content_type.model
        serializer_class = CONTENT_SERIALIZER_MAP.get(model_name)
        if not serializer_class:
            return None
        return serializer_class(instance.content_object, context=self.context).data

    def create(self, validated_data):
        section = validated_data["section"]
        content_type_name = self.context.get("content_type")  # ✅ from URL

        model_serializer_class = CONTENT_SERIALIZER_MAP.get(content_type_name)
        if not model_serializer_class:
            raise serializers.ValidationError(f"Invalid content_type: {content_type_name}")

        request = self.context.get("request")
        item_data = self.context.get("item_data", {})

        serializer = model_serializer_class(data=item_data, context=self.context)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        return SectionItem.objects.create(
            section=section,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id
        )


from django.db import transaction
# ==========================
# SECTION SERIALIZER
# ==========================
class SectionSerializer(serializers.ModelSerializer):
    items = SectionItemSerializer(many=True, read_only=True)
    page_id = serializers.CharField(write_only=True, required=True)  # ✅ required
    page_slug = serializers.SlugField(write_only=True, required=False)   # ✅ optional
    is_active = serializers.BooleanField(required=False, default=True)

    pages = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            "id",
            "title",
            "slug",
            "order",
            "is_active",
            "items",
            "page_id",
            "page_slug",
            "pages",
        ]

    def get_pages(self, obj):
        page_sections = PageSection.objects.filter(
            section=obj, is_active=True
        ).select_related("page")
        return [
            {"id": ps.page.id, "title": ps.page.title, "slug": ps.page.slug}
            for ps in page_sections
        ]

    # ✅ Validate page_id (mandatory) + optional slug
    def validate(self, attrs):
        page_id = attrs.get("page_id")
        page_slug = attrs.get("page_slug")

        if not page_id:
            raise serializers.ValidationError({"page_id": "This field is required."})

        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            raise serializers.ValidationError({"page_id": f"Page with id '{page_id}' does not exist."})

        if page_slug and page.slug != page_slug:
            raise serializers.ValidationError(
                {"page_slug": f"Slug '{page_slug}' does not match page id {page_id}."}
            )

        # ✅ stash resolved page for later use in create()
        attrs["page_obj"] = page
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        raw_items = parse_items_from_request(request.data)
        items_data = validated_data.pop("items", [])
        page = validated_data.pop("page_obj")   # ✅ from validate()
        validated_data.pop("page_id", None)
        validated_data.pop("page_slug", None)

        # --- Pre-validate items
        validated_items = []
        for idx, item_data in enumerate(raw_items or items_data):
            item_serializer = SectionItemSerializer(
                data=item_data,
                context={**self.context, "index": idx, "item_data": item_data},
            )
            item_serializer.is_valid(raise_exception=True)
            validated_items.append(item_serializer)

        # --- Atomic transaction
        with transaction.atomic():
            section = Section.objects.create(**validated_data)

            for item_serializer in validated_items:
                item_serializer.save(section=section)

            PageSection.objects.create(page=page, section=section, is_active=True)

        return section
# ==========================
# PAGESECTION SERIALIZER
# ==========================
# class PageSectionSerializer(serializers.ModelSerializer):
#     page_title = serializers.CharField(source="page.title", read_only=True)
#     section_title = serializers.CharField(source="section.title", read_only=True)

#     class Meta:
#         model = PageSection
#         fields = ["id", "page", "page_title", "section", "section_title", "order", "is_active"]

#     def validate(self, attrs):
#         page = attrs.get('page')
#         section = attrs.get('section')
#         if PageSection.objects.filter(page=page, section=section).exists():
#             raise serializers.ValidationError("This page already has this section linked.")
#         return attrs


class PageSectionSerializer(serializers.ModelSerializer):
    page_title = serializers.CharField(source="page.title", read_only=True)
    section_title = serializers.CharField(source="section.title", read_only=True)

    class Meta:
        model = PageSection
        fields = ["id", "page", "page_title", "section", "section_title", "order", "is_active"]

    def validate(self, attrs):
        page = attrs.get("page")
        section = attrs.get("section")

        # ✅ enforce uniqueness: (page_id, section_id)
        qs = PageSection.objects.filter(page=page, section=section)
        if self.instance:
            # If updating, exclude current record
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                {"non_field_errors": [f"Page '{page.id}' already has section '{section.id}' linked."]}
            )
        return attrs