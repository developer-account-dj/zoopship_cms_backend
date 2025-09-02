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
class pageminiserailizer(serializers.ModelSerializer):
    class Meta:
        model=Page
        fields = ["id","slug", "title", "is_active"]

from django.core.files.storage import default_storage
from drf_extra_fields.fields import Base64ImageField
class SectionSerializer(serializers.ModelSerializer):
    pages = pageminiserailizer(read_only=True, many=True)  # show all linked pages
    
    class Meta:
        model = Section
        fields = ["id", "slug", "is_active", "title", "section_type", "order", "data", "pages"]

    def validate_data(self, value):
        """
        Handle Base64 images in 'data' dict, including handling the 'image' key and nested structures like 'members'.
        """
        # Recursive function to handle nested structures
        def handle_images(data):
            if isinstance(data, list):
                for item in data:
                    handle_images(item)
            elif isinstance(data, dict):
                for key, file_data in data.items():
                    if key == "image" and isinstance(file_data, str) and file_data.startswith("data:image"):
                        # Convert Base64 string to InMemoryUploadedFile
                        base64_field = Base64ImageField()
                        file_obj = base64_field.to_internal_value(file_data)
                        
                        # Save to default storage
                        file_path = default_storage.save(f'sections/{file_obj.name}', file_obj)
                        data[key] = default_storage.url(file_path)
                    else:
                        # Recursively process nested dictionaries or lists
                        handle_images(file_data)
    
        # Process the 'data' dictionary
        handle_images(value)
    
        return value
    
    def to_representation(self, instance):
        """
        Serialize data, fixing media URLs in the 'data' field.
        """
        rep = super().to_representation(instance)
        
        request = self.context.get("request")
        data = rep.get("data", {})
    
        # Recursive function to handle nested structures
        def handle_media_urls(data):
            if isinstance(data, list):
                for item in data:
                    handle_media_urls(item)  # Recursively handle each item in the list
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith("/media/") and request:
                        # Convert relative media URL to absolute URL
                        data[key] = request.build_absolute_uri(value)
                    else:
                        # Recursively process nested dictionaries or lists
                        handle_media_urls(value)
    
        # Handle the 'data' dictionary
        handle_media_urls(data)
    
        rep["data"] = data
        return rep

class PageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

    children = serializers.SerializerMethodField()
    parent_title = serializers.CharField(source="parent.title", read_only=True)

    # 🔁 ManyToMany field now
    sections = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    section_details = SectionSerializer(source="sections", many=True, read_only=True)

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
            "sections",         # accepts list of IDs
            "section_details",  # returns nested section info
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
        section_objs = validated_data.pop("sections", [])
        page = super().create(validated_data)

        if section_objs:
            page.sections.set(section_objs)  # ✅ correct way for M2M
        return page

    def update(self, instance, validated_data):
        section_objs = validated_data.pop("sections", None)
        page = super().update(instance, validated_data)

        if section_objs is not None:
            page.sections.set(section_objs)  # ✅ reset to given sections
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
    # page_id = serializers.IntegerField(required=False, write_only=True)
    page_id = serializers.CharField(required=False, write_only=True)
    page_slug = serializers.SlugField(required=False, write_only=True)
    sections = SectionSerializer(many=True)

    def create(self, validated_data):
        sections_data = validated_data.pop("sections")
        page_id = validated_data.get("page_id")
        page_slug = validated_data.get("page_slug")

        # 🔎 Resolve page
        page = None
        if page_id and page_slug:
            try:
                page_by_id = Page.objects.get(id=page_id)
            except Page.DoesNotExist:
                raise serializers.ValidationError({"page_id": f"Page with id '{page_id}' does not exist"})

            try:
                page_by_slug = Page.objects.get(slug=page_slug)
            except Page.DoesNotExist:
                raise serializers.ValidationError({"page_slug": f"Page with slug '{page_slug}' does not exist"})

            if page_by_id.id != page_by_slug.id:
                raise serializers.ValidationError("page_id and page_slug do not match the same page")

            page = page_by_id
        elif page_id:
            try:
                page = Page.objects.get(id=page_id)
            except Page.DoesNotExist:
                raise serializers.ValidationError({"page_id": f"Page with id '{page_id}' does not exist"})
        elif page_slug:
            try:
                page = Page.objects.get(slug=page_slug)
            except Page.DoesNotExist:
                raise serializers.ValidationError({"page_slug": f"Page with slug '{page_slug}' does not exist"})
        else:
            raise serializers.ValidationError("Either page_id or page_slug must be provided")

        # ✅ Create sections and assign page via M2M
        created_sections = []
        for section_data in sections_data:
            section = Section.objects.create(**section_data)  # 👈 don't pass page
            section.pages.add(page)  # 👈 assign page properly
            created_sections.append(section)

        return {"sections": created_sections, "page": page}



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

