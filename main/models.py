# Create your models here.
from django.db import models, transaction
from django.db.models import Sum, F
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index= True)
    
    def __str__(self):
        return self.name
    

class Book(models.Model):
    judul = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    publisher = models.CharField(max_length=255, blank=True)
    kategori = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="books")
    
    stok = models.PositiveIntegerField()
    harga = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Untuk discount 
    diskon_persen = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["judul"]),
            models.Index(fields=["author"]),
        ]
    
    def clean(self):
        if self.diskon_persen < 0 or self.diskon_persen > 100:
            raise ValidationError("Diskon harus antara 0-100%")
    
    def get_harga_diskon(self):
        return self.harga - (self.harga * self.diskon_persen / Decimal("100"))
    
    def __str__(self):
        return f"{self.judul} - {self.author}"
    

class Sale(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    total_harga = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    total_harga = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def update_total(self):
        total = self.items.aggregate(
            total=Sum(F("harga_final") * F("kuantitas"))
        )["total"] or Decimal("0.00")

        self.total_harga = total
        self.save(update_fields=["total_harga"])

    def __str__(self):
        return f"Sale #{self.id}"

        
        
    def __str__(self):
        return f"Sale #{self.id}"
    

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
       
    # snapshot untuk transaksi
    judul_buku = models.CharField(max_length=255)
    isbn_buku = models.CharField(max_length=20)
    
    harga_asli = models.DecimalField(max_digits=12, decimal_places=2)
    diskon_persen = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    harga_final = models.DecimalField(max_digits=12, decimal_places=2)
    
    kuantitas = models.PositiveIntegerField()
    
    class Meta:
        indexes = [
            models.Index(fields=["judul_buku"]),
        ]
    
    def __str__(self):
        return f"{self.book.judul} x {self.kuantitas}"
