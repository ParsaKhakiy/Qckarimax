from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from order.service import create_order, get_orders
from order.serializers import OrderInputSerializer, OrderOutputSerializer

from .models import OrderHistoryCreator
from .permissions import IsSalesExpert
from .serializers import SalesExpertStatisticsSerializer

# --- Logic Layer ---
def create_order_history(order, seller):
    return OrderHistoryCreator.objects.create(order=order, saler=seller)


def logic_order_seller(request: Request, data: dict):
    order = create_order(
        saler=request.sales_profile,
        customer_name=data["customer_name"],
        customer_family=data["customer_family"],
        address=data["address"],
        postal_code=data["postal_code"],
        city=data["city"],
        product=data["product"],
        total_price=data["total_price"],
    )
    history = create_order_history(order, request.sales_profile)
    return order, history


# --- API Layer ---
class OrderBySellerApiView(APIView):
    permission_classes = [IsSalesExpert]

    @swagger_auto_schema(
        operation_summary="ثبت سفارش توسط کارشناس فروش",
        operation_description="این API سفارش را ثبت کرده و به صورت خودکار به تاریخچه کارشناس اضافه می‌کند.",
        request_body=OrderInputSerializer,
        responses={
            201: OrderOutputSerializer,
            400: "خطا در اعتبارسنجی داده‌ها",
            403: "عدم دسترسی کارشناس",
        },
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = OrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order, _ = logic_order_seller(request, serializer.validated_data)
        result = OrderOutputSerializer(order).data

        return Response(result, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="دریافت لیست سفارش‌ها",
        responses={
            200: OrderOutputSerializer(many=True),
            400: "خطا در پردازش داده‌ها",
            403: "عدم دسترسی کارشناس",
        },
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        try:
            orders = get_orders(request.sales_profile)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        data = OrderOutputSerializer(orders, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class DashbordApiView(APIView):
    permission_classes = [IsSalesExpert]
     
    OutputSerializer = SalesExpertStatisticsSerializer 

    @swagger_auto_schema(
        operation_summary="پروفایل محصول خرید",
        responses={
            200: SalesExpertStatisticsSerializer(),
            400: "خطا در پردازش داده‌ها",
            403: "عدم دسترسی کارشناس",
        },
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        try:
            serializer = SalesExpertStatisticsSerializer(
                request.sales_profile
            )
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)



# views/order.py
from rest_framework import generics, permissions
from rest_framework.response import Response
from order.models import Order
from order.serializers import OrderOutputSerializer
from .permissions import IsSalesExpert

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderOutputSerializer
    permission_classes = [IsSalesExpert]
    
    def get_queryset(self):
        # فقط سفارش‌های خود کارشناس
        return Order.objects.filter(saler=self.request.sales_profile)