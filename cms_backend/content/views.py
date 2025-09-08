from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from .models import (
    Page, FAQ, BlogPost, Banner, ContactInfo, HowItWorks,
    Impression, Feature,  Slide, SliderBanner, Section,SectionType,PageSection
)
from .serializers import (
    PageSerializer, FAQSerializer, BlogPostSerializer, BannerSerializer,
    NavigationSerializer, ContactInfoSerializer, HowItWorksSerializer,
    ImpressionSerializer, FeatureSerializer,
    SliderBannerSerializer, SlideSerializer, SectionSerializer
)
from core.utils.response_helpers import success_response, error_response
# ==========================
# BASEVIEWSET VIEWSET
# ==========================

class BaseViewSet(viewsets.ModelViewSet):
    """
    Base viewset to handle CRUD with success/error responses.
    All endpoints are public (no authentication required).
    """

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user if self.request.user.is_authenticated else None,
            updated_by=self.request.user if self.request.user.is_authenticated else None,
        )

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user if self.request.user.is_authenticated else None
        )

    # CREATE (POST)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return success_response(
                data=serializer.data,
                message=f"{self.basename.title()} created successfully",
                http_status=status.HTTP_201_CREATED,
            )
        return error_response(
            message="Validation failed",
            data=serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST,
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
                message=f"{self.basename.title()} updated successfully",
            )
        return error_response(
            message="Validation failed",
            data=serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    # PARTIAL UPDATE (PATCH)
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # LIST (GET)
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True)
        return success_response(
            data=serializer.data,
            message=f"{self.basename.title()} list fetched"
        )

    # RETRIEVE (GET by ID/slug)
    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            data=serializer.data,
            message=f"{self.basename.title()} fetched"
        )

    # DESTROY (DELETE)
    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return success_response(message=f"{self.basename.title()} deleted successfully")

    # 🔓 All endpoints are public
    def get_permissions(self):
        return [AllowAny()]

# ==========================
# PAGE VIEWSET
# ==========================
# class PageViewSet(BaseViewSet):
#     queryset = Page.objects.all()
#     serializer_class = PageSerializer
#     lookup_field = "id"
#     lookup_url_kwarg = "slug"

#     def get_queryset(self):
#         queryset = Page.objects.all()

#         if self.action == "retrieve":
#             # ✅ Only active when retrieving a single page
#             return queryset.filter(is_active=True).order_by("created_at")

#         if self.action == "list":
#             # ✅ return root-level pages (children nested) → all, active + inactive
#             return queryset.filter(parent_id__isnull=True).order_by("created_at")

#         return queryset.order_by("created_at")

class PageViewSet(BaseViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    lookup_field = "id"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        queryset = Page.objects.all()

        # Filter by page_type (optional)
        page_types = self.request.query_params.getlist("page_type")
        if page_types:
            # MySQL JSONField contains check
            from django.db.models import Q
            q = Q()
            for pt in page_types:
                q |= Q(page_type__icontains=pt)
            queryset = queryset.filter(q)

        if self.action == "retrieve":
            return queryset.filter(is_active=True).order_by("created_at")

        if self.action == "list":
            return queryset.filter(parent_id__isnull=True).order_by("created_at")

        return queryset.order_by("created_at")

    def get_object(self):
        """
        - GET (retrieve) → lookup by slug (only active)
        - PUT/PATCH/DELETE → lookup by id (all, active + inactive)
        """
        queryset = Page.objects.all()

        if self.action == "retrieve":
            queryset = queryset.filter(is_active=True)  # only active for single GET
            lookup_field = "slug"
        else:
            lookup_field = "id"

        lookup_url_kwarg = self.lookup_url_kwarg or lookup_field
        filter_kwargs = {lookup_field: self.kwargs[lookup_url_kwarg]}
        return get_object_or_404(queryset, **filter_kwargs)

    def list(self, request, *args, **kwargs):
        if request.query_params.get("type") == "navigation":
            # ✅ Navigation → root-level active only
            root_pages = Page.objects.filter(
                parent_id__isnull=True, is_active=True
            ).order_by("created_at")
            serializer = NavigationSerializer(root_pages, many=True)
            return success_response(data=serializer.data, message="Navigation fetched")

        # ✅ Default list → all root pages (active + inactive) with children
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Pages fetched")
    

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # check if page has children
        if instance.children.exists():
            return Response(
                {
                    "success": False,
                    "message": "Unable to delete. This page has child pages.",
                    "data": []
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_destroy(instance)
        return Response(
            {
                "success": True,
                "message": "Page deleted successfully.",
                "data": []
            },
            status=status.HTTP_200_OK
        )
    



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
        # For list endpoint → return ALL banners (active & inactive)
        if self.action == "list":
            return Banner.objects.all().order_by("created_at")
        return super().get_queryset()

    def get_object(self):
        """
        - Retrieve by `slug` (only active banners)
        - Update/Delete by `id`
        """
        if self.action == "retrieve":
            slug = self.kwargs.get("pk")  # DRF uses "pk" in URL conf
            try:
                obj = Banner.objects.get(slug=slug, is_active=True)
            except Banner.DoesNotExist:
                raise NotFound(detail="No active banner found with this slug.")
            return obj

        # For update/delete → fallback to default (id lookup)
        return super().get_object()

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


class SliderBannerViewSet(BaseViewSet):
    queryset = SliderBanner.objects.all().order_by("created_at")
    serializer_class = SliderBannerSerializer
    lookup_field = "pk"  # default → use "pk" (can be slug or id)

    def get_object(self):
        lookup_value = self.kwargs.get("pk")

        # 🔹 Try slug lookup first (only active banners)
        try:
            return SliderBanner.objects.get(slug=lookup_value, is_active=True)
        except SliderBanner.DoesNotExist:
            pass

        # 🔹 Fallback to ID lookup
        try:
            return SliderBanner.objects.get(pk=lookup_value)
        except (SliderBanner.DoesNotExist, ValueError):
            raise NotFound("Slider banner not found.")
        
    # 🔹 explicit slug-based retrieve endpoint
    @action(detail=False, methods=["get"], url_path="by-slug/(?P<slug>[^/.]+)")
    def retrieve_by_slug(self, request, slug=None):
        try:
            slider = SliderBanner.objects.get(slug=slug, is_active=True)
        except SliderBanner.DoesNotExist:
            raise NotFound("No active slider banner found with this slug.")

        return success_response(
            data=SliderBannerSerializer(slider).data,
            message="Slider banner retrieved successfully",
        )
    

       # 🚫 Prevent delete if slides exist
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if any slides are attached
        if instance.slides.exists():
            return error_response(
                message="Cannot delete slider banner because slides exist. Delete slides first.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # If no slides → allow delete
        self.perform_destroy(instance)
        return success_response(
            message="Slider banner deleted successfully",
            http_status=status.HTTP_200_OK,
        )


    # 🔹 Create slider with nested slides (form-data)
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        slides_data = []
        index = 0
        while f"slides[{index}][heading]" in data:
            slides_data.append({
                "heading": data.get(f"slides[{index}][heading]"),
                "description": data.get(f"slides[{index}][description]"),
                "image": request.FILES.get(f"slides[{index}][image]"),
            })
            index += 1

        slider_serializer = SliderBannerSerializer(data={
            "title": data.get("title"),
            "is_active": data.get("is_active", True),
        })

        if slider_serializer.is_valid():
            slider = slider_serializer.save()
            for slide in slides_data:
                Slide.objects.create(slider=slider, **slide)
            return success_response(
                data=SliderBannerSerializer(slider).data,
                message="Slider banner created successfully",
                http_status=status.HTTP_201_CREATED,
            )
        return error_response(
            message="Validation failed",
            data=slider_serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    # 🔹 Update slider with nested slides (form-data)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        data = request.data.copy()

        # Collect incoming slides by order
        slides_data = []
        index = 0
        while (
            f"slides[{index}][heading]" in data
            or f"slides[{index}][description]" in data
            or f"slides[{index}][image]" in request.FILES
        ):
            slides_data.append({
                "heading": data.get(f"slides[{index}][heading]"),
                "description": data.get(f"slides[{index}][description]"),
                "image": request.FILES.get(f"slides[{index}][image]"),
            })
            index += 1

        # Update banner fields
        slider_serializer = SliderBannerSerializer(
            instance,
            data={"title": data.get("title"), "is_active": data.get("is_active", instance.is_active)},
            partial=partial
        )

        if slider_serializer.is_valid():
            slider = slider_serializer.save()

            existing_slides = list(slider.slides.all().order_by("created_at"))

            # Update or create slides based on order
            for i, slide_data in enumerate(slides_data):
                if i < len(existing_slides):  # update existing
                    slide = existing_slides[i]
                    for attr, value in slide_data.items():
                        if value is not None:
                            setattr(slide, attr, value)
                    slide.save()
                else:  # create new slide
                    Slide.objects.create(slider=slider, **{k: v for k, v in slide_data.items() if v})

            return success_response(
                data=SliderBannerSerializer(slider).data,
                message="Slider banner updated successfully",
            )

        return error_response(
            message="Validation failed",
            data=slider_serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    # ✅ Add slide
    @action(detail=True, methods=["post"], url_path="slides")
    def add_slide(self, request, slug=None):
        slider = self.get_object()
        serializer = SlideSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(slider=slider)
            return success_response(
                data=serializer.data,
                message="Slide added successfully",
                http_status=status.HTTP_201_CREATED,
            )
        return error_response(
            message="Validation failed",
            data=serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    # ✅ Update slide
    @action(detail=True, methods=["patch"], url_path="slides/(?P<slide_id>[^/.]+)")
    def update_slide(self, request, slug=None, slide_id=None):
        try:
            slide = Slide.objects.get(pk=slide_id, slider__slug=slug)
        except Slide.DoesNotExist:
            raise NotFound("Slide not found")

        serializer = SlideSerializer(slide, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(
                data=serializer.data,
                message="Slide updated successfully",
            )
        return error_response(
            message="Validation failed",
            data=serializer.errors,
            http_status=status.HTTP_400_BAD_REQUEST,
        )
    

    # ✅ Delete slide
    @action(detail=True, methods=["delete"], url_path="slides/(?P<slide_id>[^/.]+)")
    def delete_slide(self, request, pk=None, slide_id=None):   # 👈 pk, not slug
        try:
            slide = Slide.objects.get(pk=slide_id, slider__pk=pk)
        except Slide.DoesNotExist:
            raise NotFound("Slide not found")
        slide.delete()
        return success_response(message="Slide deleted successfully")

    
# ==========================
# Section ViewSet
# ==========================
from .serializers import SectionSerializer, SectionListSerializer
from rest_framework import parsers
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, NotFound

class SectionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "Section list fetched",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "data": data,
        })

from django.db.models import Prefetch
class SectionViewSet(BaseViewSet):
    serializer_class = SectionSerializer
    lookup_field = "id"
    parser_classes = [parsers.JSONParser]
    pagination_class = SectionPagination

    # ✅ Only select required fields and prefetch pages
    queryset = Section.objects.only(
        "id", "slug", "title", "section_type", "order", "data"
    ).prefetch_related(
        Prefetch(
            "pagesection_set",
            queryset=PageSection.objects.select_related("page").only("page_id", "is_active")
        )
    ).order_by("order")


    def get_serializer_class(self):
        if self.action == "create" and "sections" in self.request.data:
            return SectionListSerializer
        return SectionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({
            "success": True,
            "message": "Sections created successfully",
            "data": SectionSerializer(result['sections'], many=True, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # ✅ If pagination is requested
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        # ✅ Return all sections without pagination
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response({
            "success": True,
            "message": "Section list fetched",
            "count": queryset.count(),
            "next": None,
            "previous": None,
            "data": serializer.data
        })
    

    def get_queryset(self):
        queryset = super().get_queryset()
        page_slug = self.request.query_params.get("page_slug")
        page_id = self.request.query_params.get("page_id")
        section_slug = self.request.query_params.get("section_slug")
        section_id = self.request.query_params.get("section_id")
        section_type = self.request.query_params.get("section_type")
    
        # ✅ Validation: prevent conflicting filters
        if page_id and page_slug:
            raise ValidationError("Provide either 'page_id' or 'page_slug', not both.")
        if section_id and section_slug:
            raise ValidationError("Provide either 'section_id' or 'section_slug', not both.")
    
        # ✅ Filter by page
        if page_id:
            queryset = queryset.filter(pages__id=page_id)
        elif page_slug:
            queryset = queryset.filter(pages__slug=page_slug)
    
        # ✅ Filter by section id/slug
        if section_id:
            queryset = queryset.filter(id=section_id)
        elif section_slug:
            queryset = queryset.filter(slug=section_slug)
    
        # ✅ Filter by section_type (works with/without page filters)
        if section_type:
            queryset = queryset.filter(section_type=section_type)
    
        return queryset

    def patch(self, request, *args, **kwargs):
        section_id = request.query_params.get("section_id")
        page_id = request.query_params.get("page_id")
    
        if not section_id or not page_id:
            return Response(
                {"success": False, "message": "Both section_id and page_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # Update global section fields
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {"success": False, "message": f"Section {section_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
        section_data = request.data.copy()
        is_active = section_data.pop("is_active", None)
    
        serializer = self.get_serializer(section, data=section_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    
        # Update per-page is_active
        try:
            page_section = PageSection.objects.get(page_id=page_id, section_id=section_id)
            if is_active is not None:
                page_section.is_active = is_active
                page_section.save()
        except PageSection.DoesNotExist:
            return Response(
                {"success": False, "message": f"Section {section_id} not assigned to Page {page_id}"},
                status=status.HTTP_404_NOT_FOUND
            )
    
        return Response({
            "success": True,
            "message": f"Section {section_id} updated successfully for Page {page_id}.",
            "data": serializer.data | {"is_active": page_section.is_active}
        }, status=status.HTTP_200_OK)
    
    
    def delete(self, request, *args, **kwargs):
        section_id = request.query_params.get("section_id")
        page_id = request.query_params.get("page_id")
    
        if not section_id or not page_id:
            return Response(
                {"detail": "Both section_id and page_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {"detail": f"Section with id '{section_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return Response(
                {"detail": f"Page with id '{page_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    
        # ❌ Don't delete the whole section
        # ✅ Just remove the relation to that page
        section.pages.remove(page)
    
        return Response(
            {"detail": f"Section {section_id} unassigned from page {page_id}"},
            status=status.HTTP_204_NO_CONTENT,
        )
    
    def destroy(self, request, *args, **kwargs):
        """Permanently delete a Section from DB."""
        section_id = kwargs.get("id")

        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {"success": False, "message": f"Section with id '{section_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        section.delete()
        return Response(
            {"success": True, "message": f"Section {section_id} deleted permanently"},
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=['post'], url_path='assigned')
    def assign_section(self, request):
        """
        Assign a section to a page.
        Expects `page_id` and `section_id` in query parameters.
        """
        page_id = request.query_params.get("page_id")
        section_id = request.query_params.get("section_id")

        if not page_id or not section_id:
            return Response(
                {"success": False, "message": "Both section_id and page_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the page and section
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return Response(
                {"detail": f"Page with id '{page_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {"detail": f"Section with id '{section_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Assign the section to the page
        if section.pages.filter(id=page.id).exists():
            return Response(
                {"detail": f"Section {section_id} is already assigned to page {page_id}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        section.pages.add(page)

        return Response(
            {"detail": f"Section {section_id} successfully assigned to page {page_id}"},
            status=status.HTTP_201_CREATED
        )
    

    @action(detail=False, methods=['post'], url_path='unassigned')
    def unassign_section(self, request):
        """
        Unassign a section from a page.
        Expects `page_id` and `section_id` in query parameters.
        """
        page_id = request.query_params.get("page_id")
        section_id = request.query_params.get("section_id")

        if not page_id or not section_id:
            return Response(
                {"success": False, "message": "Both section_id and page_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the page and section
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return Response(
                {"detail": f"Page with id '{page_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {"detail": f"Section with id '{section_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if the section is already unassigned
        if not section.pages.filter(id=page.id).exists():
            return Response(
                {"detail": f"Section {section_id} is not assigned to page {page_id}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove the relation between section and page (unassign)
        section.pages.remove(page)

        return Response(
            {"detail": f"Section {section_id} successfully unassigned from page {page_id}"},
            status=status.HTTP_204_NO_CONTENT
        )