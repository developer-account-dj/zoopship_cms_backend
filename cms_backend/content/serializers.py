from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .models import (
    Page, FAQ, BlogPost, Banner, HowItWorks,
    Impression, Feature, ContactInfo,
    Section, PageSection
)

User = get_user_model()


# ==========================
# PAGE SERIALIZER
# ==========================
class PageSectionSerializer(serializers.ModelSerializer):
    section_title = serializers.CharField(source="section.title", read_only=True)
    section_type = serializers.CharField(source="section.type", read_only=True)
    # Optional: include section items if you want
    section_items = serializers.SerializerMethodField()

    class Meta:
        model = PageSection
        fields = ["id", "section", "section_title", "section_type", "order", "is_active", "section_items"]

    def get_section_items(self, obj):
        # Only include items if section is active
        if obj.section.is_active:
            return [{"id": item.id, "object_id": item.object_id} for item in obj.section.items.all()]
        return []


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
            "parent",
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
        page_sections = PageSection.objects.filter(
            page=obj, is_active=True
        ).order_by("order")
        return PageSectionSerializer(page_sections, many=True).data

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by("order")
        return PageSerializer(children, many=True).data


# ==========================
# FAQ SERIALIZER
# ==========================
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'


# ==========================
# BLOG SERIALIZER
# ==========================
class BlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = BlogPost
        fields = '__all__'
        read_only_fields = ('author',)

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user
        return super().create(validated_data)


# ==========================
# BANNER SERIALIZER
# ==========================
class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'


# ==========================
# HOW IT WORKS SERIALIZER
# ==========================
class HowItWorksSerializer(serializers.ModelSerializer):
    class Meta:
        model = HowItWorks
        fields = '__all__'


# ==========================
# IMPRESSION SERIALIZER
# ==========================
class ImpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impression
        fields = '__all__'


# ==========================
# FEATURE SERIALIZER
# ==========================
class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = '__all__'


# ==========================
# NAVIGATION SERIALIZER
# ==========================
class NavigationSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "title", "slug", "children", "order"]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by("order")
        return NavigationSerializer(children, many=True).data


# ==========================
# CONTACT INFO SERIALIZER
# ==========================
class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ['id', 'contact_type', 'label', 'value', 'icon', 'order', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


# ==========================
# SECTION SERIALIZER
# ==========================
from .models import Section, SectionItem

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from .models import Section, SectionItem

class SectionItemSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()  # accept simple type like "faq" or "banner"
    content_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SectionItem
        fields = ['content_type', 'content_object']

    def validate(self, attrs):
        content_type_str = attrs.get('content_type')

        # Map simple type to app_label.model
        type_map = {
            'faq': 'content.faq',
            'banner': 'content.banner',
            'blog_post': 'content.blogpost',
            'navigation_item': 'content.navigationitem',
            'contact_info': 'content.contactinfo',
            'how_it_works': 'content.howitworks',
            'impression': 'content.impression',
            'feature': 'content.feature',
        }

        if content_type_str not in type_map:
            raise serializers.ValidationError(f"Invalid content_type '{content_type_str}'")

        app_label, model = type_map[content_type_str].split('.')
        ct = ContentType.objects.get(app_label=app_label, model=model)

        attrs['content_type'] = ct
        attrs['simple_type'] = content_type_str  # store for response

        return attrs

    def get_content_object(self, obj):
        content_obj = obj.content_object
        if content_obj and getattr(content_obj, 'is_active', True):
            return str(content_obj)
        return None


class SectionSerializer(serializers.ModelSerializer):
    items = SectionItemSerializer(many=True, required=False)

    class Meta:
        model = Section
        fields = ['id', 'title', 'is_active', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        section = Section.objects.create(**validated_data)

        for item_data in items_data:
            ct = item_data['content_type']
            simple_type = item_data['simple_type']

            if ct.model == "page":
                SectionItem.objects.create(
                    section=section,
                    content_type=ct,
                    object_id=item_data.get('object_id')
                )
            else:
                model_class = ct.model_class()
                for obj in model_class.objects.filter(is_active=True):
                    SectionItem.objects.create(
                        section=section,
                        content_type=ct,
                        object_id=obj.id
                    )

        return section

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                ct = item_data['content_type']
                simple_type = item_data['simple_type']

                if ct.model == "page":
                    SectionItem.objects.create(
                        section=instance,
                        content_type=ct,
                        object_id=item_data.get('object_id')
                    )
                else:
                    model_class = ct.model_class()
                    for obj in model_class.objects.filter(is_active=True):
                        SectionItem.objects.create(
                            section=instance,
                            content_type=ct,
                            object_id=obj.id
                        )

        return instance

    def to_representation(self, instance):
        """Return simplified content_type in response"""
        rep = super().to_representation(instance)
        items = rep.get('items', [])
        for idx, item in enumerate(items):
            item_obj = instance.items.all()[idx]
            # Map ContentType back to simple type
            model_name = item_obj.content_type.model
            item['content_type'] = model_name  # simple type like "faq", "banner"
        return rep
    

from .models import PageSection, Page, Section

class PageSectionSerializer(serializers.ModelSerializer):
    page_title = serializers.CharField(source='page.title', read_only=True)
    section_title = serializers.CharField(source='section.title', read_only=True)

    class Meta:
        model = PageSection
        fields = ['id', 'page', 'page_title', 'section', 'section_title', 'order', 'is_active']

    def validate(self, attrs):
        # Ensure unique combination
        page = attrs.get('page')
        section = attrs.get('section')
        if PageSection.objects.filter(page=page, section=section).exists():
            raise serializers.ValidationError("This page already has this section linked.")
        return attrs