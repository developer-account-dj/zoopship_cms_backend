from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet,FAQViewSet,BlogPostViewSet,BannerViewSet

router = DefaultRouter()
router.register('pages', PageViewSet, basename='page')
router.register('faqs', FAQViewSet, basename='faq')
router.register('blogposts', BlogPostViewSet, basename='blogpost')
router.register('banners', BannerViewSet, basename='banner')

urlpatterns = [
    path('', include(router.urls)),
]