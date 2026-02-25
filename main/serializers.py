from rest_framework import serializers
from .models import Book, Category, Sale, SaleItem


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