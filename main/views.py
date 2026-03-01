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
from rest_framework.decorators import action


# Create your views here.

    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class CheckoutView(APIView):

    @transaction.atomic
    def post(self, request, cart_id):
        try:
            cart = Cart.objects.prefetch_related("items__book").get(
                id=cart_id,
                is_checked_out=False
            )
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart tidak ditemukan atau sudah checkout"},
                status=404
            )

        if not cart.items.exists():
            return Response({"error": "Cart kosong"}, status=400)

        sale = Sale.objects.create()

        for item in cart.items.all():
            book = Book.objects.select_for_update().get(id=item.book.id)
            if book.stok < item.kuantitas:
                return Response(
                    {"error": f"Stok tidak cukup untuk {book.judul}"},
                    status=400
                )

            Book.objects.filter(id=book.id).update(stok=F("stok") - item.kuantitas)

            SaleItem.objects.create(
                sale=sale,
                book=book,
                judul_buku=book.judul,
                isbn_buku=book.isbn,
                harga_asli=book.harga,
                diskon_persen=book.diskon_persen,
                harga_final=book.get_harga_diskon(),
                kuantitas=item.kuantitas
            )

        sale.update_total()

        # tandain cart yg udh ckeout
        cart.is_checked_out = True
        cart.save(update_fields=["is_checked_out"])

        # Hapus item di cart lma
        cart.items.all().delete()

        # buat cart bru
        new_cart = Cart.objects.create(is_checked_out=False)

        return Response({
            "sale_id": sale.id,
            "total_harga": sale.total_harga,
            "new_cart_id": new_cart.id
        }, status=201)
        
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

    # buat filter, blm imple,entasi
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["kategori", "is_active"]
    search_fields = ["judul", "author", "isbn"]
    ordering_fields = ["harga", "stok", "judul"]

    # nambh stok buku
    @action(detail=True, methods=['post'])
    def add_stock(self, request, pk=None):
        book = self.get_object()
        qty = int(request.data.get("quantity", 1))
        book.stok += qty
        book.save(update_fields=["stok"])
        return Response({'status': 'stok ditambah', 'stok': book.stok})

    # kurngin sotk buku
    @action(detail=True, methods=['post'])
    def reduce_stock(self, request, pk=None):
        book = self.get_object()
        qty = int(request.data.get("quantity", 1))
        if book.stok >= qty:
            book.stok -= qty
            book.save(update_fields=["stok"])
            return Response({'status': 'stok dikurangi', 'stok': book.stok})
        else:
            return Response({'error': 'stok tidak cukup'}, status=status.HTTP_400_BAD_REQUEST)
    
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
        
from rest_framework.viewsets import ModelViewSet
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(ModelViewSet):
    queryset = Cart.objects.all().prefetch_related("items__book")
    serializer_class = CartSerializer
    
    
class CartItemViewSet(ModelViewSet):
    queryset = CartItem.objects.select_related("book", "cart")
    serializer_class = CartItemSerializer

    
    def create(self, request, *args, **kwargs):
        cart_id = request.data.get("cart")
        book_id = request.data.get("book")
        qty = int(request.data.get("kuantitas", 1))

        if not cart_id or not Cart.objects.filter(id=cart_id, is_checked_out=False).exists():
            cart = Cart.objects.create(is_checked_out=False)
            cart_id = cart.id
            
        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, book_id=book_id)
            cart_item.kuantitas += qty
            cart_item.save(update_fields=["kuantitas"])
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            serializer = self.get_serializer(data={
                "cart": cart_id,
                "book": book_id,
                "kuantitas": qty
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    # nmbh kuantitas
    @action(detail=True, methods=['post'])
    def increment(self, request, pk=None):
        item = self.get_object()
        item.kuantitas += 1
        item.save(update_fields=['kuantitas'])
        return Response({'status': 'kuantitas ditambah', 'kuantitas': item.kuantitas})

    # Decrment kuantitas
    @action(detail=True, methods=['post'])
    def decrement(self, request, pk=None):
        item = self.get_object()
        if item.kuantitas > 1:
            item.kuantitas -= 1
            item.save(update_fields=['kuantitas'])
            return Response({'status': 'kuantitas dikurangi', 'kuantitas': item.kuantitas})
        else:
            item.delete()
            return Response({'status': 'item dihapus'})

    # hpus item dlm cart

    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        cart_id = request.data.get("cart")
        CartItem.objects.filter(cart_id=cart_id).delete()
        return Response({'status': 'cart dikosongkan'}, status=status.HTTP_204_NO_CONTENT)