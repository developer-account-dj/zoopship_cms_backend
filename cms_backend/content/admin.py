from django.contrib import admin
from .models import (
    Page, FAQ, BlogPost, Banner, HowItWorks, Feature, Impression, Section, ContactInfo, PageSection
)

# -------------------------
# Page Admin
# -------------------------
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "slug", "parent", "order", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "content", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("parent__id", "order")  # parent-child ordering
    actions = ["publish_pages", "unpublish_pages"]

    @admin.action(description="Publish selected pages")
    def publish_pages(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} page(s) successfully published.")

    @admin.action(description="Unpublish selected pages")
    def unpublish_pages(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} page(s) successfully unpublished.")


# -------------------------
# Section Admin
# -------------------------
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "created_at", "updated_at")
    search_fields = ("title",)
    ordering = ("title",)
    actions = ["activate_sections", "deactivate_sections"]

    @admin.action(description="Activate selected sections")
    def activate_sections(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} section(s) successfully activated.")

    @admin.action(description="Deactivate selected sections")
    def deactivate_sections(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} section(s) successfully deactivated.")


# -------------------------
# FAQ Admin
# -------------------------
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "is_active", "order", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")
    ordering = ("order",)
    actions = ["activate_faqs", "deactivate_faqs"]

    @admin.action(description="Activate selected FAQs")
    def activate_faqs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} FAQ(s) successfully activated.")

    @admin.action(description="Deactivate selected FAQs")
    def deactivate_faqs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} FAQ(s) successfully deactivated.")


# -------------------------
# Banner Admin
# -------------------------
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    actions = ["activate_banners", "deactivate_banners"]

    @admin.action(description="Activate selected banners")
    def activate_banners(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} banner(s) successfully activated.")

    @admin.action(description="Deactivate selected banners")
    def deactivate_banners(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} banner(s) successfully deactivated.")


# -------------------------
# Blog Post Admin
# -------------------------
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "slug", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "author")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    actions = ["publish_posts", "unpublish_posts"]

    @admin.action(description="Publish selected blog posts")
    def publish_posts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} blog post(s) successfully published.")

    @admin.action(description="Unpublish selected blog posts")
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} blog post(s) successfully unpublished.")


# -------------------------
# Feature Admin
# -------------------------
@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "order", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    ordering = ("order",)
    readonly_fields = ("created_at", "updated_at")


# -------------------------
# HowItWorks Admin
# -------------------------
@admin.register(HowItWorks)
class HowItWorksAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subtitle", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "subtitle", "description")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Main Information", {"fields": ("title", "subtitle", "description", "background_image", "is_active")}),
        ("Steps Information", {"fields": ("steps",)}),
        ("Extra Data", {"fields": ("extra_fields",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# -------------------------
# Impression Admin
# -------------------------
@admin.register(Impression)
class ImpressionAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "title", "is_active", "description", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("is_active", "created_at", "updated_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# -------------------------
# ContactInfo Admin
# -------------------------
@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ("contact_type", "label", "value", "icon", "order", "is_active", "created_at")
    list_filter = ("contact_type", "is_active")
    search_fields = ("label", "value")
    ordering = ("contact_type", "order")


# -------------------------
# PageSection Admin
# -------------------------
@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "section", "order", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "page")
    search_fields = ("page__title", "section__title")
    ordering = ("page", "order")
