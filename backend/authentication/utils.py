
from django.http import HttpRequest

def set_sessionjwt(
    request:HttpRequest ,
    access_token , 
    refresh_token,
    *args , 
    **kwargs


)->None:
    if 'access' in request.session:
        del request.session['access']
        del request.session['refresh']
        print('remove acesss ')

    print("*"*20 , '\n')
    print('acesss' , access_token ,'\n')
    print("*"*20)
    
    assert request , 'Request Must not Null'
    request.session['access'] = access_token
    request.session['refresh'] = refresh_token
    if args :
        for arg in args:
            request.session[f'{args}'] = args
    
    if kwargs:
        for k , v in kwargs:
            request.session[str(k)] = v
