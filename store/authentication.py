from django.contrib.auth.backends import BaseBackend
from store.models import User
from django.db.models import Q 
from django.contrib.auth import get_user_model


User=get_user_model()

class EmailBackend(BaseBackend):

    def authenticate(self, request, username =None, password=None,**kwargs):
        
        try:
            # Look up the user by email instead of username
            user_object=User.objects.get(email=username)          #Q(phone=username)|Q(email=username)
                                                                  #for sign in with phone number but phone field set into Unique
            if user_object.check_password(password):

                return user_object           # Return the user if password is correct
            
        except User.DoesNotExist:

            return None

        return None
    
    def get_user(self, user_id):

        try:

            return User.objects.get(id=user_id)
        
        except User.DoesNotExist:

            return None