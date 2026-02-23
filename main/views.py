from django.shortcuts import render
from rest_framework.pagination import PageNumberPagination

# Create your views here.
class BookPagination(PageNumberPagination):
    page_size = 5
    
class SalePagination(PageNumberPagination):
    page_size = 10