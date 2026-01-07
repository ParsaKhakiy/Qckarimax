from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpRequest



class JwtSessionMiddleware(MiddlewareMixin):
    

    def process_request(self, request:HttpRequest):
        if 'access' in request.session:
            try : 
                jwt_authtication = JWTAuthentication()
                

                validated_token = jwt_authtication.get_validated_token(request.session['access'])
                user = jwt_authtication.get_user(validated_token)

                request.user = user 
                print(
                    "User from Auth" , user
                )
            except BaseException as e :
                print(
                    'error' , e
                )
    
        
        print("run jwt middleware")


# middleware/jwt_auth.py
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken , TokenError

def get_user_from_token(access_token: str):
    """
    گرفتن کاربر از اکسس توکن JWT
    :param access_token: رشته توکن JWT
    :return: شیء User یا None
    """
    try:
        # 1. توکن رو اعتبارسنجی کن
        token = AccessToken(access_token)
        
        # 2. user_id رو از توکن بگیر
        user_id = token['user_id']
        
        # 3. کاربر رو از دیتابیس بگیر
        user = get_user_model().objects.get(id=user_id)
        
        return user
        
    except TokenError as e:
        print(f"❌ مشکل توکن: {e}")
        return None
    except get_user_model().DoesNotExist:
        print("❌ کاربر وجود ندارد")
        return None
    except Exception as e:
        print(f"⚠️ خطای ناشناخته: {e}")
        return None
from django.contrib.auth import get_user_model






class JwtSessionMiddleware(MiddlewareMixin):
    """
    میدل‌ور برای احراز هویت با JWT در هر درخواست
    """
    
    def process_request(self, request):
        """
        چک کردن توکن JWT و تنظیم user روی request
        """
        # فقط اگه توکن بود چک کن
        if 'access' in request.session:
            
        
            user = get_user_from_token(request.session['access'])
            if user :
                request.user = user 
    
            print('request user is', request.user)

            
            
