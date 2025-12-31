from backend.utils.apis import BaseCRUDViewSet 

from .models import Product
from rest_framework.serializers import ModelSerializer

class TestproductSeraizlier(ModelSerializer):
    class Meta:
        model = Product 
        fields = '__all__'


class TestProduct(BaseCRUDViewSet):
    queryset = Product.objects.all()
    input_serializer_class = TestproductSeraizlier
    output_serializer_class = TestproductSeraizlier 
