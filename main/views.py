from django.shortcuts import render
from .pagination import BookPagination, SalePagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from .models import Category, Book, Sale, SaleItem
from .serializers import CategorySerializer, BookSerializer, SaleItemSerializer, SaleSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from django.db.models import Sum, F
from django.utils.dateparse import parse_date
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.viewsets import ReadOnlyModelViewSet


# Create your views here.

    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class CheckoutView(APIView):
    @transaction.atomic
    def post(self, request):
        items = request.data.get("items", [])

        if not items:
            return Response(
                {"error": "Tidak ada item"},
                status=status.HTTP_400_BAD_REQUEST
            )

        sale = Sale.objects.create()

        for item in items:
            try:
                book = Book.objects.select_for_update().get(id=item["book_id"])
            except Book.DoesNotExist:
                return Response({"error": "Buku tidak ditemukan"}, status=404)
            
            qty = item["kuantitas"]
            if qty <= 0:
                return Response({"error": "Jumlah barang tidak ada"}, status=400)

            if book.stok < qty:
                return Response(
                    {"error": f"Stok tidak cukup untuk {book.judul}"},
                    status=400
                )

            # Kurangi stok secara atomic
            Book.objects.filter(id=book.id).update(
                stok=F("stok") - qty
            )

            harga_asli = book.harga
            diskon = book.diskon_persen
            harga_final = book.get_harga_diskon()

            SaleItem.objects.create(
                sale=sale,
                book=book,
                judul_buku=book.judul,
                isbn_buku=book.isbn,
                harga_asli=harga_asli,
                diskon_persen=diskon,
                harga_final=harga_final,
                kuantitas=qty
            )

        sale.update_total()

        return Response({
            "sale_id": sale.id,
            "total_harga": sale.total_harga
        }, status=status.HTTP_201_CREATED)
        
class DailyReportView(APIView):

    def get(self, request):
        today = timezone.now().date()

        total = Sale.objects.filter(
            created_at__date=today
        ).aggregate(
            total=Sum("total_harga")
        )["total"] or Decimal("0.00")

        total_transaksi = Sale.objects.filter(
            created_at__date=today
        ).count()

        return Response({
            "tanggal": today,
            "total_transaksi": total_transaksi,
            "total_penjualan": total
        })
        
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
class BookViewSet(ModelViewSet):
    queryset = Book.objects.all().select_related("kategori")
    serializer_class = BookSerializer
    pagination_class = BookPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ["kategori", "is_active"]
    search_fields = ["judul", "author", "isbn"]
    ordering_fields = ["harga", "stok", "judul"]
    
class SaleViewSet(ReadOnlyModelViewSet):
    queryset = Sale.objects.all().prefetch_related("items")
    serializer_class = SaleSerializer
    pagination_class = SalePagination
    
class ReportView(APIView):

    def get(self, request):
        start_date = parse_date(request.GET.get("start"))
        end_date = parse_date(request.GET.get("end"))
        
        if start_date and end_date and start_date > end_date:
            return Response({"error": "Range tanggal tidak valid"}, status=400)
        
        sales = Sale.objects.all()

        if start_date and end_date:
            sales = sales.filter(
                created_at__date__range=[start_date, end_date]
            )

        total_penjualan = sales.aggregate(
            total=Sum("total_harga")
        )["total"] or Decimal("0.00")

        total_transaksi = sales.count()

        best_seller = SaleItem.objects.filter(
            sale__in=sales
        ).values("judul_buku").annotate(
            total_terjual=Sum("kuantitas")
        ).order_by("-total_terjual").first()

        return Response({
            "total_penjualan": total_penjualan,
            "total_transaksi": total_transaksi,
            "best_seller": best_seller
        })