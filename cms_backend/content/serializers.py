from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import (
    Page, FAQ, BlogPost, Banner, HowItWorks,
    Impression, Feature, ContactInfo, Slide, SliderBanner,Section,SectionType
)
User = get_user_model()


# ==========================
# PAGE SERIALIZER
# ==========================

class PageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

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
    


class SectionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionType
        fields = ["id", "name", "description", "schema", "created_at", "updated_at"]

class SectionSerializer(serializers.ModelSerializer):
    section_type = SectionTypeSerializer(read_only=True)
    section_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SectionType.objects.all(), source="section_type", write_only=True
    )
    page_id = serializers.PrimaryKeyRelatedField(
        queryset=Page.objects.all(), source="page", write_only=True
    )

    class Meta:
        model = Section
        fields = [
            "id", "page", "page_id", "section_type", "section_type_id",
            "content", "position", "created_at", "updated_at"
        ]
        depth = 1
    

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

