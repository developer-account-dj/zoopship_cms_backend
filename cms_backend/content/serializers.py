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
def parse_items_from_request(request_data):
    """
    Convert flat POST keys like items[0][title] -> [{'title': ...}, {...}]
    Works for multipart/form-data with file fields too.
    """
    items_dict = {}

    for key, value in request_data.items():
        if not key.startswith("items["):
            continue
        # e.g. "items[0][title]" -> idx=0, field="title"
        inside = key[len("items["):]
        idx_str, field = inside.split("]", 1)
        idx = int(idx_str)
        field = field.strip("[]")

        if idx not in items_dict:
            items_dict[idx] = {}
        items_dict[idx][field] = value

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

# ==========================
# SECTION ITEM SERIALIZER
# ==========================

class SectionItemSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.CharField(read_only=True)

    # Add nested representation of the related content object
    content_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SectionItem
        fields = ["id", "content_type", "object_id", "content_object"]

    def get_content_object(self, instance):
        model_name = instance.content_type.model  # e.g. "faq", "banner"
        serializer_class = CONTENT_SERIALIZER_MAP.get(model_name)
        if not serializer_class:
            return None
        return serializer_class(instance.content_object, context=self.context).data

    def create(self, validated_data):
        section = validated_data["section"]
        content_type_name = validated_data.pop("content_type").lower()

        model_serializer_class = CONTENT_SERIALIZER_MAP.get(content_type_name)
        if not model_serializer_class:
            raise serializers.ValidationError(f"Invalid content_type: {content_type_name}")

        # Item data already pre-parsed from request
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
    page_slug = serializers.SlugField(write_only=True, required=False)
    is_active = serializers.BooleanField(required=False, default=True)

    pages = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["id", "title", "slug", "is_active", "items", "page_slug", "pages"]

    def get_pages(self, obj):
        page_sections = PageSection.objects.filter(section=obj, is_active=True).select_related("page")
        return [
            {
                "id": ps.page.id,
                "title": ps.page.title,
                "slug": ps.page.slug,
            }
            for ps in page_sections
        ]

    def create(self, validated_data):
        request = self.context.get("request")

        raw_items = parse_items_from_request(request.data)
        items_data = validated_data.pop("items", [])
        page_slug = validated_data.pop("page_slug", None)

        # 1. Pre-validate items BEFORE creating section
        validated_items = []
        for idx, item_data in enumerate(raw_items or items_data):
            item_serializer = SectionItemSerializer(
                data=item_data,
                context={**self.context, "index": idx, "item_data": item_data},
            )
            item_serializer.is_valid(raise_exception=True)
            validated_items.append(item_serializer)

        # 2. Atomic transaction
        with transaction.atomic():
            section = Section.objects.create(**validated_data)

            # Save pre-validated items
            for item_serializer in validated_items:
                item_serializer.save(section=section)

            # Handle page_slug safely
            if page_slug:
                try:
                    page = Page.objects.get(slug=page_slug)
                except Page.DoesNotExist:
                    raise serializers.ValidationError(
                        {"page_slug": f"Page with slug '{page_slug}' does not exist."}
                    )
                PageSection.objects.create(page=page, section=section, is_active=True)

        return section

# ==========================
# PAGESECTION SERIALIZER
# ==========================
class PageSectionSerializer(serializers.ModelSerializer):
    page_title = serializers.CharField(source="page.title", read_only=True)
    section_title = serializers.CharField(source="section.title", read_only=True)

    class Meta:
        model = PageSection
        fields = ["id", "page", "page_title", "section", "section_title", "order", "is_active"]

    def validate(self, attrs):
        page = attrs.get('page')
        section = attrs.get('section')
        if PageSection.objects.filter(page=page, section=section).exists():
            raise serializers.ValidationError("This page already has this section linked.")
        return attrs