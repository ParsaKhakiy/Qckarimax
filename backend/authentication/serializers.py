from django.utils.module_loading import import_string

from django.conf import settings 
from django.contrib.auth.models import update_last_login

from typing import Any


# must install django simple rest 
# TokenObtainClass = import_string(
#     settings.TOKEN_OBTAIN_SERIALIZER
# )
from .utils import set_sessionjwt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



class TokenObtainClassc(TokenObtainPairSerializer):
    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        
        # if settings.UPDATE_LAST_LOGIN:
        #     update_last_login(None, self.user)

        set_sessionjwt(
            self.context.get('request'),
            access_token=data['access'],
            refresh_token=data['refresh'],
            )

        
        return data