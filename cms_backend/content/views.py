from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .models import (
    Page, FAQ, BlogPost, Banner, NavigationItem,
    ContactInfo, HowItWorks, Impression, Feature, Section
)
from .serializers import (
    PageSerializer, FAQSerializer, BlogPostSerializer, BannerSerializer,
    NavigationItemSerializer, ContactInfoSerializer, HowItWorksSerializer,
    ImpressionSerializer, FeatureSerializer, SectionSerializer
)
from core.utils.response_helpers import success_response, error_response


# ==========================
# BASE VIEWSET
# ==========================
class BaseViewSet(viewsets.ModelViewSet):
    """
    Base viewset to handle create/update/destroy with success/error responses.
    Other viewsets inherit from this.
    """

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True)
        return success_response(data=serializer.data, message=f"{self.basename.title()} list fetched")

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data, message=f"{self.basename.title()} fetched")

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return success_response(message=f"{self.basename.title()} deleted")


# ==========================
# PAGE VIEWSET
# ==========================
class PageViewSet(BaseViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return Page.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# FAQ VIEWSET
# ==========================
class FAQViewSet(BaseViewSet):
    queryset = FAQ.objects.all().order_by("order")
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return FAQ.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# BLOGPOST VIEWSET
# ==========================
class BlogPostViewSet(BaseViewSet):
    queryset = BlogPost.objects.all().order_by("-created_at")
    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return BlogPost.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# BANNER VIEWSET
# ==========================
class BannerViewSet(BaseViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return Banner.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# NAVIGATION VIEWSET
# ==========================
class NavigationViewSet(BaseViewSet):
    queryset = NavigationItem.objects.all()
    serializer_class = NavigationItemSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.action == "list":
            return NavigationItem.objects.filter(parent__isnull=True, is_active=True).order_by("order")
        return super().get_queryset()


# ==========================
# CONTACT INFO VIEWSET
# ==========================
class ContactInfoViewSet(BaseViewSet):
    queryset = ContactInfo.objects.all()
    serializer_class = ContactInfoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return ContactInfo.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# HOW IT WORKS VIEWSET
# ==========================
class HowItWorksViewSet(BaseViewSet):
    queryset = HowItWorks.objects.all()
    serializer_class = HowItWorksSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return HowItWorks.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# IMPRESSION VIEWSET
# ==========================
class ImpressionViewSet(BaseViewSet):
    queryset = Impression.objects.all()
    serializer_class = ImpressionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return Impression.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# FEATURE VIEWSET
# ==========================
class FeatureViewSet(BaseViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return Feature.objects.filter(is_active=True).order_by("-created_at")


# ==========================
# SECTION VIEWSET
# ==========================
class SectionViewSet(BaseViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return Section.objects.filter(is_active=True).order_by("-created_at")



from .models import PageSection
from .serializers import PageSectionSerializer

class PageSectionViewSet(viewsets.ModelViewSet):
    queryset = PageSection.objects.all()
    serializer_class = PageSectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # def get_queryset(self):
    #     return PageSection.objects.filter(is_active=True,section__is_active=True).order_by("-created_at")


