from django.contrib.auth import get_user_model
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import (
    ActiveBorrowingsFilterBackend,
    AvailableBooksFilterBackend,
    BookFilter,
    BorrowingFilter,
    MinPagesFilterBackend,
)
from .models import Author, Book, Borrowing
from .serializers import (
    AuthorSerializer,
    BookDetailSerializer,
    BookSerializer,
    BorrowingSerializer,
    ReaderRegisterSerializer,
)
from .throttles import (
    BorrowingRateThrottle,
    BurstRateThrottle,
    RegisterRateThrottle,
    SustainedRateThrottle,
)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


def landing_page(request):
    return render(request, "index.html")


class ReaderRegisterAPIView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = ReaderRegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, RegisterRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reader = serializer.save()

        refresh = RefreshToken.for_user(reader)
        response_data = {
            **serializer.data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class CountDataListMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"count": queryset.count(), "data": serializer.data})


class AuthorListCreateAPIView(CountDataListMixin, generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class AuthorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_url_kwarg = "author_id"


class BookListCreateAPIView(CountDataListMixin, generics.ListCreateAPIView):
    queryset = Book.objects.select_related("author").all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = BookFilter
    filter_backends = [DjangoFilterBackend, MinPagesFilterBackend]
    throttle_classes = [
        AnonRateThrottle,
        UserRateThrottle,
        BurstRateThrottle,
        SustainedRateThrottle,
    ]


class BookDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.select_related("author").prefetch_related("borrowings")
    serializer_class = BookDetailSerializer
    permission_classes = [IsAdminOrReadOnly]


class BorrowingListCreateAPIView(CountDataListMixin, generics.ListCreateAPIView):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BorrowingFilter
    throttle_classes = [UserRateThrottle, BorrowingRateThrottle]

    def get_queryset(self):
        return Borrowing.objects.select_related("book", "reader").filter(
            reader=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(reader=self.request.user)


class AvailableBooksAPIView(CountDataListMixin, generics.ListAPIView):
    queryset = Book.objects.select_related("author").order_by("pk")
    serializer_class = BookSerializer
    filterset_class = BookFilter
    filter_backends = [DjangoFilterBackend, AvailableBooksFilterBackend]


class ActiveBorrowingsAPIView(CountDataListMixin, generics.ListAPIView):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BorrowingFilter
    filter_backends = [DjangoFilterBackend, ActiveBorrowingsFilterBackend]
    throttle_classes = [UserRateThrottle, BorrowingRateThrottle]

    def get_queryset(self):
        return Borrowing.objects.select_related("book", "reader").filter(
            reader=self.request.user
        ).order_by("-borrowed_date")
