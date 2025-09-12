from django.contrib import admin
from .models import (
    Page,Section, PageSection,MetaPixelCode
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
    list_display = ("id", "title", "page_type","slug","name","parent_id","is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "content", "slug")
    prepopulated_fields = {"slug": ("title",)}
    actions = ["activate_items", "deactivate_items"]




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
        # "order",
        "created_at",
        "updated_at",
    )
    search_fields = ("id", "title", "slug")
    # ordering = ("order", "id")
    inlines = [PageSectionInline]

    # Show related pages as a comma-separated list
    def get_pages(self, obj):
        return ", ".join(obj.pages.values_list("name", flat=True)) or "-"
    get_pages.short_description = "Pages"

   


# -------------------------
# PageSection Admin
# -------------------------
@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "section", "is_active","order")
    list_filter = ("is_active", "page__slug", "section__section_type")
    search_fields = ("page__title", "section__title", "section__slug")
    ordering = ("id",)



@admin.register(MetaPixelCode)
class MetaPixelCodeAdmin(admin.ModelAdmin):
    list_display = ("id",'page', 'add_title_meta')
    search_fields = ('page__title', 'add_title_meta', 'google_pixel_code', 'facebook_pixel_code')
    list_filter = ('page',)
    ordering = ('page',)