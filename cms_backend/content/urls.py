# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PageViewSet, FAQViewSet, BlogPostViewSet, BannerViewSet,
    ContactInfoViewSet, HowItWorksViewSet, FeatureViewSet,
    ImpressionViewSet, SliderBannerViewSet, SectionViewSet,PageSectionViewSet
)

# ==========================
# Router Registration
# ==========================
router = DefaultRouter()
router.register(r'pages', PageViewSet, basename='page')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'blogposts', BlogPostViewSet, basename='blogpost')
router.register(r'banners', BannerViewSet, basename='banner')
router.register(r'contact-info', ContactInfoViewSet, basename='contactinfo')
router.register(r'how-it-works', HowItWorksViewSet, basename='how-it-works')
router.register(r'impressions', ImpressionViewSet, basename='impression')
router.register(r'features', FeatureViewSet, basename='feature')
# router.register(r'sections', SectionViewSet, basename='section')   # ✅ enabled
router.register(r'page-sections', PageSectionViewSet, basename='pagesection')  # ✅ new
router.register(r'slider-banners', SliderBannerViewSet, basename='sliderbanner')
# router.register(r'sections/(?P<content_type>[\w-]+)', SectionViewSet, basename='section')
router.register(r'sections/(?P<content_type>[\w-]+)',SectionViewSet,basename='section')

# With content_type + page_slug
router.register(
    r'sections/(?P<content_type>[\w-]+)/(?P<page_slug>[\w-]+)',
    SectionViewSet,
    basename='section-by-page'
)

urlpatterns = [
    path('', include(router.urls)),
]
