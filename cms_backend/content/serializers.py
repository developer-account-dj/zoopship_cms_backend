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
    

class pageminiserailizer(serializers.ModelSerializer):
    class Meta:
        model=Page
        fields = ["id","slug", "title", "is_active"]


from django.core.files.storage import default_storage
from drf_extra_fields.fields import Base64ImageField
class SectionSerializer(serializers.ModelSerializer):
    page = pageminiserailizer(read_only=True)
    
    class Meta:
        model = Section
        fields = ["id", "slug","is_active", "title","sectiontype", "order", "data", "page",]

    def validate_data(self, value):
        """
        Handle Base64 images in 'data' dict.
        """
        for key, file_data in value.items():
            if isinstance(file_data, str) and file_data.startswith("data:image"):
                # Convert Base64 string to InMemoryUploadedFile
                base64_field = Base64ImageField()
                file_obj = base64_field.to_internal_value(file_data)
                # Save to default storage
                file_path = default_storage.save(f'sections/{file_obj.name}', file_obj)
                value[key] = default_storage.url(file_path)
        return value
    

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        request = self.context.get("request")
        data = rep.get("data", {})

        # Fix media paths inside data dict
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("/media/") and request:
                data[key] = request.build_absolute_uri(value)

        rep["data"] = data
        return rep


class SectionListSerializer(serializers.Serializer):
    # page_id = serializers.IntegerField(required=False, write_only=True)
    page_id = serializers.CharField(required=False, write_only=True) 
    page_slug = serializers.SlugField(required=False, write_only=True)
    sections = SectionSerializer(many=True)

    def create(self, validated_data):
        sections_data = validated_data.pop("sections")
        page_id = validated_data.get("page_id")
        page_slug = validated_data.get("page_slug")
    
        page = None
    
        if page_id and page_slug:
            # Both provided: check they match the same page
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
            
            page = page_by_id  # both match
    
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
    
        created_sections = []
        for section_data in sections_data:
            section = Section.objects.create(page=page, **section_data)
            created_sections.append(section)
    
        return {"sections": created_sections, "page": page}  # Include page for response

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

