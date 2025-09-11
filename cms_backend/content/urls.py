# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PageViewSet, SectionViewSet,SectionOrderListAPIView
)

# ==========================
# Router Registration
# ==========================
router = DefaultRouter()
router.register(r'pages', PageViewSet, basename='page')
# router.register(r'section-types', SectionTypeViewSet, basename='section-type')
router.register(r'sections',SectionViewSet, basename='section')

urlpatterns = [
    path('', include(router.urls)),
    path('section/order/', SectionOrderListAPIView.as_view(), name='section-order-list'),
    
]
