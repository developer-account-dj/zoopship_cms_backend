# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PageViewSet, FAQViewSet, BlogPostViewSet, BannerViewSet,
    ContactInfoViewSet, HowItWorksViewSet, FeatureViewSet,
    ImpressionViewSet, SliderBannerViewSet
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
router.register(r'slider-banners', SliderBannerViewSet, basename='sliderbanner')


urlpatterns = [
    path('', include(router.urls)),
]
