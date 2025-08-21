from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .models import (
    Page, FAQ, BlogPost, Banner,
    ContactInfo, HowItWorks, Impression, Feature, Section, PageSection
)
from .serializers import (
    PageSerializer, FAQSerializer, BlogPostSerializer, BannerSerializer,
    NavigationSerializer, ContactInfoSerializer, HowItWorksSerializer,
    ImpressionSerializer, FeatureSerializer, SectionSerializer, PageSectionSerializer
)
from core.utils.response_helpers import success_response, error_response
from django.shortcuts import get_object_or_404

# ==========================
# BASE VIEWSET
# ==========================
# class BaseViewSet(viewsets.ModelViewSet):
#     """
#     Base viewset to handle create/update/destroy with success/error responses.
#     Other viewsets inherit from this.
#     """

#     def perform_create(self, serializer):
#         serializer.save(created_by=self.request.user, updated_by=self.request.user)

#     def perform_update(self, serializer):
#         serializer.save(updated_by=self.request.user)

#     def list(self, request, *args, **kwargs):
#         serializer = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True)
#         return success_response(data=serializer.data, message=f"{self.basename.title()} list fetched")

#     def retrieve(self, request, *args, **kwargs):
#         serializer = self.get_serializer(self.get_object())
#         return success_response(data=serializer.data, message=f"{self.basename.title()} fetched")

#     def destroy(self, request, *args, **kwargs):
#         self.get_object().delete()
#         return success_response(message=f"{self.basename.title()} deleted")

#     # Common permission logic
#     def get_permissions(self):
#         if self.action in ["list", "retrieve"]:
#             return [AllowAny()]
#         return [IsAuthenticated()]

class BaseViewSet(viewsets.ModelViewSet):
    """
    Base viewset to handle create/update/destroy with success/error responses.
    Other viewsets inherit from this.
    """

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    # CREATE (POST)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return success_response(
                data=serializer.data,
                message=f"{self.basename.title()} created successfully",
                http_status=status.HTTP_201_CREATED
            )
        return error_response(
            message="Validation failed",
            data=serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST
        )

    # UPDATE (PUT)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return success_response(
                data=serializer.data,
                message=f"{self.basename.title()} updated successfully"
            )
        return error_response(
            message="Validation failed",
            data=serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST
        )

    # PARTIAL UPDATE (PATCH)
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # LIST (GET)
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True)
        return success_response(data=serializer.data, message=f"{self.basename.title()} list fetched")

    # RETRIEVE (GET by ID/slug)
    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data, message=f"{self.basename.title()} fetched")

    # DESTROY (DELETE)
    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return success_response(message=f"{self.basename.title()} deleted successfully")

    # Common permission logic
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]


# ==========================
# PAGE VIEWSET
# ==========================
# class PageViewSet(BaseViewSet):
#     queryset = Page.objects.all()
#     serializer_class = PageSerializer
#     lookup_field = "slug"

#     def get_queryset(self):
#         if self.action == "list":
#             return Page.objects.filter(is_active=True).order_by("-created_at")
#         return super().get_queryset()



class PageViewSet(BaseViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if self.action == "list":
            # ✅ only fetch root-level pages
            return Page.objects.filter(parent__isnull=True, is_active=True).order_by("order")
        return super().get_queryset()

    # Custom endpoint for navigation
    def list(self, request, *args, **kwargs):
        if request.query_params.get("type") == "navigation":
            root_pages = Page.objects.filter(parent__isnull=True, is_active=True).order_by("order")
            serializer = NavigationSerializer(root_pages, many=True)
            return success_response(data=serializer.data, message="Navigation fetched")

        return super().list(request, *args, **kwargs)


# ==========================
# FAQ VIEWSET
# ==========================
class FAQViewSet(BaseViewSet):
    queryset = FAQ.objects.all().order_by("order")
    serializer_class = FAQSerializer

    def get_queryset(self):
        if self.action == "list":
            return FAQ.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()


# ==========================
# BLOGPOST VIEWSET
# ==========================
class BlogPostViewSet(BaseViewSet):
    queryset = BlogPost.objects.all().order_by("-created_at")
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        if self.action == "list":
            return BlogPost.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()


# ==========================
# BANNER VIEWSET
# ==========================
class BannerViewSet(BaseViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer

    def get_queryset(self):
        if self.action == "list":
            return Banner.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()


# ==========================
# CONTACT INFO VIEWSET
# ==========================
class ContactInfoViewSet(BaseViewSet):
    queryset = ContactInfo.objects.all()
    serializer_class = ContactInfoSerializer

    def get_queryset(self):
        if self.action == "list":
            return ContactInfo.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()


# ==========================
# HOW IT WORKS VIEWSET
# ==========================
class HowItWorksViewSet(BaseViewSet):
    queryset = HowItWorks.objects.all()
    serializer_class = HowItWorksSerializer

    def get_queryset(self):
        if self.action == "list":
            return HowItWorks.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()


# ==========================
# IMPRESSION VIEWSET
# ==========================
class ImpressionViewSet(BaseViewSet):
    queryset = Impression.objects.all()
    serializer_class = ImpressionSerializer

    def get_queryset(self):
        if self.action == "list":
            return Impression.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()


# ==========================
# FEATURE VIEWSET
# ==========================
class FeatureViewSet(BaseViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer

    def get_queryset(self):
        if self.action == "list":
            return Feature.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()


# ==========================
# SECTION VIEWSET
# ==========================
class SectionViewSet(BaseViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if self.action == "list":
            return Section.objects.filter(is_active=True).order_by("-created_at")
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Sections fetched successfully",
            "data": serializer.data
        })

    def retrieve(self, request, slug=None):
        section = get_object_or_404(Section, slug=slug)
        serializer = self.get_serializer(section)
        return Response({
            "success": True,
            "message": "Section retrieved successfully",
            "data": serializer.data
        })


# ==========================
# PAGE SECTION VIEWSET
# ==========================
class PageSectionViewSet(BaseViewSet):
    queryset = PageSection.objects.all()
    serializer_class = PageSectionSerializer

    def get_queryset(self):
        if self.action == "list":
            return PageSection.objects.filter(is_active=True, section__is_active=True).order_by("-created_at")
        return super().get_queryset()
    
