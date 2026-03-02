from django.core.management.base import BaseCommand
from decimal import Decimal
from main.models import Category, Book, Cart, CartItem
from django.db import connection

class Command(BaseCommand):
    help = 'Seeder kategori, buku, cart (SQLite, ID mulai dari 1)'

    #  NOTE: RESET SEQUENCE DAN DELATE KALO DB UDH ADA DATA DRI SBLMNYA, KLO BLM ADA GA USH DELATE
    def reset_sequence(self, model_class):
        table_name = model_class._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
        self.stdout.write(f"Sequence {table_name} reset")

    def handle(self, *args, **options):
        self.stdout.write("Deleting old data...")
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Book.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write("Resetting sequences...")
        self.reset_sequence(Category)
        self.reset_sequence(Book)
        self.reset_sequence(Cart)

        # Kategori
        self.stdout.write("Creating categories...")
        categories = ["Thriller", "Fantasi", "Romatis", "Horror", "Science Fiction"]
        category_objs = {}
        for name in categories:
            obj, _ = Category.objects.get_or_create(name=name)
            category_objs[name] = obj
            self.stdout.write(f"Category: {obj.name}")

        # Buku
        self.stdout.write("Creating books...")
        books = [
            # Thriller (2 buku)
            {
                "judul": "Buku Thriller 1",
                "author": "Author A",
                "isbn": "1234567890123",
                "publisher": "Publisher A",
                "kategori": category_objs["Thriller"],
                "stok": 5,
                "harga": Decimal("120000.00"),
                "diskon_persen": Decimal("0.00"),
                "is_active": True,
            },
            {
                "judul": "Buku Thriller 2",
                "author": "Author B",
                "isbn": "1234567890124",
                "publisher": "Publisher B",
                "kategori": category_objs["Thriller"],
                "stok": 5,
                "harga": Decimal("150000.00"),
                "diskon_persen": Decimal("5.00"),
                "is_active": True,
            },
            # Fantasi (3 buku)
            {
                "judul": "Buku Fantasi 1",
                "author": "Author C",
                "isbn": "2234567890123",
                "publisher": "Publisher C",
                "kategori": category_objs["Fantasi"],
                "stok": 10,
                "harga": Decimal("100000.00"),
                "diskon_persen": Decimal("0.00"),
                "is_active": True,
            },
            {
                "judul": "Buku Fantasi 2",
                "author": "Author D",
                "isbn": "2234567890124",
                "publisher": "Publisher D",
                "kategori": category_objs["Fantasi"],
                "stok": 8,
                "harga": Decimal("120000.00"),
                "diskon_persen": Decimal("10.00"),
                "is_active": True,
            },
            {
                "judul": "Buku Fantasi 3",
                "author": "Author E",
                "isbn": "2234567890125",
                "publisher": "Publisher E",
                "kategori": category_objs["Fantasi"],
                "stok": 15,
                "harga": Decimal("90000.00"),
                "diskon_persen": Decimal("0.00"),
                "is_active": True,
            },
        ]

        for bdata in books:
            book, _ = Book.objects.get_or_create(isbn=bdata["isbn"], defaults=bdata)
            self.stdout.write(f"Book: {book.judul}")

        self.stdout.write("Creating cart(s)...")
        for i in range(2):
            cart = Cart.objects.create(is_checked_out=False)
            self.stdout.write(f"Cart created with ID: {cart.id}")

        self.stdout.write(self.style.SUCCESS("SEEDING SELESAI! :D"))