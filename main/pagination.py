from rest_framework.pagination import PageNumberPagination

class BookPagination(PageNumberPagination):
    page_size = 5
    
class SalePagination(PageNumberPagination):
    page_size = 10