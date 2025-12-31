from django.utils.decorators import method_decorator
from rest_framework.viewsets import ModelViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi




class BaseCRUDViewSet(ModelViewSet): #
    input_serializer_class = None 
    output_serializer_class = None 
    
    
    def get_serializer_class(self):
        """
        تعیین خودکار سریالایزر بر اساس نوع درخواست
        """
        if self.action in ['create', 'update', 'partial_update']:
            return self.input_serializer_class or self.output_serializer_class
        return self.output_serializer_class or super().get_serializer_class()

    @method_decorator(name='list', decorator=swagger_auto_schema(
        operation_description="لیست کردن آیتم‌ها",
        responses={200: openapi.Response('Success', schema= output_serializer_class)}
    ))
    def list(self, request, *args, **kwargs):
        if hasattr(self, 'customize_list'):
            return self.customize_list(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    @method_decorator(name='create', decorator=swagger_auto_schema(
        request_body=input_serializer_class,
        responses={201: output_serializer_class}
    ))
    def create(self, request, *args, **kwargs):
        if hasattr(self, 'customize_create'):
            return self.customize_create(request, *args, **kwargs)
        return super().create(request, *args, **kwargs)

    @method_decorator(name='retrieve', decorator=swagger_auto_schema(
        responses={200: output_serializer_class},
    ))
    def retrieve(self, request, *args, **kwargs):
        if hasattr(self, 'customize_retrieve'):
            return self.customize_retrieve(request, *args, **kwargs)
        return super().retrieve(request, *args, **kwargs)

    @method_decorator(name='update', decorator=swagger_auto_schema(
        request_body=input_serializer_class,
        responses={200: output_serializer_class},
        
    ))
    def update(self, request, *args, **kwargs):
        if hasattr(self, 'customize_update'):
            return self.customize_update(request, *args, **kwargs)
        return super().update(request, *args, **kwargs)