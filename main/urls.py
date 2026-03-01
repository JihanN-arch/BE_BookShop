from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    BookViewSet,
    CategoryViewSet,
    SaleViewSet,
    CheckoutView,
    ReportView,
    CartViewSet,
    CartItemViewSet,
)

router = DefaultRouter()
router.register(r"books", BookViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"sales", SaleViewSet)
router.register(r"carts", CartViewSet)
router.register(r"cart-items", CartItemViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("sales/checkout/<int:cart_id>/", CheckoutView.as_view()),
    path("sales/report/", ReportView.as_view()),
]