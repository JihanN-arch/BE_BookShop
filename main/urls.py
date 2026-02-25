from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    BookViewSet,
    CategoryViewSet,
    SaleViewSet,
    CheckoutView,
    ReportView,
)

router = DefaultRouter()
router.register(r"books", BookViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"sales", SaleViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("sales/checkout/", CheckoutView.as_view()),
    path("sales/report/", ReportView.as_view()),
]