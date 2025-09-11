from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Show these fields in the admin list view
    list_display = ("username", "email", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)

    # Add 'role' to fieldsets so it appears in the admin form
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("role",)}),
    )

# Register the custom user model with the custom admin
admin.site.register(User, CustomUserAdmin)