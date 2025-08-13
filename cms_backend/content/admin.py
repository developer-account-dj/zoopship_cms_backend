from django.contrib import admin
from .models import Page, FAQ, BlogPost, Banner

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

    actions = ['publish_pages', 'unpublish_pages']

    @admin.action(description=("Publish selected pages"))
    def publish_pages(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} page(s) successfully published.")

    @admin.action(description=("Unpublish selected pages"))
    def unpublish_pages(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} page(s) successfully unpublished.")

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("id", 'question', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    ordering = ('order',)

    actions = ['activate_faqs', 'deactivate_faqs']

    @admin.action(description=("Activate selected FAQs"))
    def activate_faqs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} FAQ(s) successfully activated.")

    @admin.action(description=("Deactivate selected FAQs"))
    def deactivate_faqs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} FAQ(s) successfully deactivated.")

from django.utils.translation import gettext_lazy as _

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'slug', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'author')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}

    actions = ['publish_posts', 'unpublish_posts']

    @admin.action(description=_("Publish selected blog posts"))
    def publish_posts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} blog post(s) successfully published.")

    @admin.action(description=_("Unpublish selected blog posts"))
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} blog post(s) successfully unpublished.")

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'start_date', 'end_date', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    
    actions = ['activate_banners', 'deactivate_banners']

    @admin.action(description=("Activate selected banners"))
    def activate_banners(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} banner(s) successfully activated.")

    @admin.action(description=("Deactivate selected banners"))
    def deactivate_banners(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} banner(s) successfully deactivated.")



from .models import NavigationItem

@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'order', 'is_active')
    list_filter = ('is_active',)
    ordering = ('order',)