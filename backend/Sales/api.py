from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from order.service import create_order , get_orders

from .models import OrderHistoryCreator
from .permissions import IsSalesExpert


def create_order_history(order, saler):
    return OrderHistoryCreator.objects.create(order=order, saler=saler)


def Logic_Order_Saler(request: Request, data, *args, **kwargs) -> Response:
    order = create_order(
        saler=request.sales_profile,
        customer_name=data.get("customer_name"),
        customer_family=data.get("customer_family"),
        address=data.get("address"),
        postal_code=data.get("postal_code"),
        city=data.get("city"),
        product=data.get("product"),
        total_price=data.get("total_price"),
    )

    history = create_order_history(order, request.sales_profile)

    return order, history



from django.utils.decorators import method_decorator
from rest_framework.status import HTTP_201_CREATED

from order.serializers import OrderInputSerializer, OrderOutputSerializer


# API LAYER
class OrderBySallerApiView(APIView):
    permission_classes = [IsSalesExpert]

    @swagger_auto_schema(
        operation_summary="ثبت سفارش توسط کارشناس فروش",
        operation_description="این API سفارش را ثبت کرده و به صورت خودکار به تاریخچه کارشناس اضافه می‌کند.",
        request_body=OrderInputSerializer,
        responses={
            201: OrderOutputSerializer,
            400: "خطا در اعتبار سنجی داده‌ها",
            403: "عدم دسترسی کارشناس",
        },
    )
    def post(request: Request, *args, **kwargs) -> Response:

        serializer = OrderInputSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        order, history = Logic_Order_Saler(request, serializer.data)

        resualt = OrderOutputSerializer(order).data

        return Response(resualt, status=HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Get order",
        responses={
            201: OrderOutputSerializer,
            400: "خطا در اعتبار سنجی داده‌ها",
            403: "عدم دسترسی کارشناس",
        },
        )
    def get(request: Request, *args, **kwargs) -> Response: # TODO add filter 
        
        try : 
            response_data = get_orders(
                request.sales_profile
            ) 
        except Exception as e : # Error handel must process in logic functions 
            return Response(
                f"{e}" , status=status.HTTP_400_BAD_REQUEST
            ) 
            
        return Response(
            OrderOutputSerializer(response_data , many = True).data ,
            status=status.HTTP_200_OK
        )
    

