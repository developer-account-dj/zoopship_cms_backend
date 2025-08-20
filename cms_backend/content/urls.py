from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PageViewSet, FAQViewSet, BlogPostViewSet, BannerViewSet,
    ContactInfoViewSet, HowItWorksViewSet, FeatureViewSet, ImpressionViewSet,
    SectionViewSet,PageSectionViewSet
)

router = DefaultRouter()
router.register(r'pages', PageViewSet, basename='page')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'blogposts', BlogPostViewSet, basename='blogpost')
router.register(r'banners', BannerViewSet, basename='banner')
router.register(r'contact-info', ContactInfoViewSet, basename='contactinfo')
router.register(r'how-it-works', HowItWorksViewSet, basename='how-it-works')
router.register(r'impressions', ImpressionViewSet, basename='impression')  # ✅ fixed naming
router.register(r'features', FeatureViewSet, basename='feature')
router.register(r'sections', SectionViewSet, basename='section')  # ✅ added SectionViewSet
router.register(r'page-sections', PageSectionViewSet, basename='pagesection')

urlpatterns = [
    path('', include(router.urls)),
]
