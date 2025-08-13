from rest_framework import serializers
from .models import Page

class PageSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    content = serializers.CharField(required=False, allow_blank=True)  # <-- make optional

    class Meta:
        model = Page
        fields = [
            'id', 'slug', 'content', 'created_at', 'updated_at',
            'name', 'title', 'is_active', 'created_by', 'updated_by'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'created_by', 'updated_by']


from content.models import FAQ

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'


from content.models import BlogPost
from django.contrib.auth import get_user_model

User = get_user_model()

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
    

from content.models import Banner

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'
