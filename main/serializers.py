from rest_framework import serializers
from .models import Book, Category, Sale, SaleItem, Cart, CartItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    harga_setelah_diskon = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "judul",
            "author",
            "isbn",
            "publisher",
            "kategori",
            "stok",
            "harga",
            "diskon_persen",
            "is_active",
            "harga_setelah_diskon",
        ]
        read_only_fields = ["harga_setelah_diskon"]

    def get_harga_setelah_diskon(self, obj):
        return obj.get_harga_diskon()


class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = [
            "id",
            "judul_buku",
            "isbn_buku",
            "harga_asli",
            "diskon_persen",
            "harga_final",
            "kuantitas",
            "created_at",
        ]
        read_only_fields = fields


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = "__all__"
        
class CartItemSerializer(serializers.ModelSerializer):
    book_detail = BookSerializer(source="book", read_only=True)  # <-- ini baru

    class Meta:
        model = CartItem
        fields = ["id", "cart", "book", "book_detail", "kuantitas"]  # tambahin book_detail

    def validate(self, data):
        if data["cart"].is_checked_out:
            raise serializers.ValidationError("Cart sudah di-checkout")
        if data["book"].stok < data["kuantitas"]:
            raise serializers.ValidationError("Stok tidak cukup")
        return data

    def validate_kuantitas(self, value):
        if value <= 0:
            raise serializers.ValidationError("Kuantitas harus lebih dari 0")
        return value

    def create(self, validated_data):
        cart = validated_data["cart"]
        book = validated_data["book"]
        qty = validated_data["kuantitas"]

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            book=book,
            defaults={"kuantitas": qty}
        )

        if not created:
            item.kuantitas += qty
            item.save(update_fields=["kuantitas"])

        return item
    
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "created_at", "is_checked_out", "items"]
        
