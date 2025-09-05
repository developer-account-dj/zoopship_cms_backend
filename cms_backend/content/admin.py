from django.contrib import admin
from .models import (
    Page,
    FAQ, BlogPost, Banner, SliderBanner, Slide,
    Feature, HowItWorks, Impression, ContactInfo,
    Section, PageSection
)

# -------------------------
# Common Admin Mixins
# -------------------------
class ActiveAdminMixin:
    """Reusable mixin for active/inactive actions."""

    @admin.action(description="Activate selected items")
    def activate_items(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} item(s) successfully activated.")

    @admin.action(description="Deactivate selected items")
    def deactivate_items(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} item(s) successfully deactivated.")


# -------------------------
# Page Admin (only once!)
# -------------------------
@admin.register(Page)
class PageAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "title", "slug", "parent_id", "order", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "content", "slug")
    prepopulated_fields = {"slug": ("title",)}
    actions = ["activate_items", "deactivate_items"]


# -------------------------
# FAQ Admin
# -------------------------
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "question", "is_active", "order", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")
    ordering = ("order",)
    actions = ["activate_items", "deactivate_items"]


# -------------------------
# Banner Admin
# -------------------------
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "title", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    actions = ["activate_items", "deactivate_items"]


# -------------------------
# Blog Post Admin
# -------------------------
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "title", "slug", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    actions = ["activate_items", "deactivate_items"]


# -------------------------
# Feature Admin
# -------------------------
@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "title", "order", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    ordering = ("order",)
    readonly_fields = ("created_at", "updated_at")
    actions = ["activate_items", "deactivate_items"]


# -------------------------
# How It Works Admin
# -------------------------
@admin.register(HowItWorks)
class HowItWorksAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "title", "subtitle", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "subtitle", "description")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    actions = ["activate_items", "deactivate_items"]

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
class ImpressionAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "type", "title", "is_active", "description", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("is_active", "created_at", "updated_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    actions = ["activate_items", "deactivate_items"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# -------------------------
# ContactInfo Admin
# -------------------------
@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("contact_type", "label", "value", "icon", "order", "is_active", "created_at")
    list_filter = ("contact_type", "is_active")
    search_fields = ("label", "value")
    ordering = ("contact_type", "order")
    actions = ["activate_items", "deactivate_items"]


# -------------------------
# Slider Banner & Slide Admin
# -------------------------
class SlideInline(admin.TabularInline):
    model = Slide
    extra = 1
    fields = ("heading", "description", "image")
    show_change_link = True


@admin.register(SliderBanner)
class SliderBannerAdmin(admin.ModelAdmin, ActiveAdminMixin):
    list_display = ("id", "title", "slug", "is_active", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug")
    list_filter = ("is_active", "created_at")
    inlines = [SlideInline]
    actions = ["activate_items", "deactivate_items"]


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("id", "heading", "slider", "created_at", "updated_at")
    search_fields = ("heading", "description")
    list_filter = ("slider", "created_at")


from .models import Section, PageSection


# -------------------------
# Inline for Section Admin
# -------------------------
class PageSectionInline(admin.TabularInline):
    """Inline editor for PageSection inside Section admin."""
    model = PageSection
    extra = 1
    autocomplete_fields = ["page"]
    fields = ["page", "is_active"]
    show_change_link = True


# -------------------------
# Section Admin
# -------------------------
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "get_pages",
        "section_type",
        "order",
        "created_at",
        "updated_at",
    )
    search_fields = ("id", "title", "slug")
    ordering = ("order", "id")
    inlines = [PageSectionInline]

    # Show related pages as a comma-separated list
    def get_pages(self, obj):
        return ", ".join(obj.pages.values_list("slug", flat=True)) or "-"
    get_pages.short_description = "Pages"

   


# -------------------------
# PageSection Admin
# -------------------------
@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "section", "is_active")
    list_filter = ("is_active", "page__slug", "section__section_type")
    search_fields = ("page__title", "section__title", "section__slug")
    ordering = ("id",)