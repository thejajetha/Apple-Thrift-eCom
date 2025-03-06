from django.contrib.auth.backends import BaseBackend
from store.models import User
from django.db.models import Q 

class EmailBackend(BaseBackend):

    def authenticate(self, request, username =None, password=None):
        
        try:
            
            user_object=User.objects.get(email=username)        #Q(phone=username)|Q(email=username)
                                                            #for sign in with phone number but phone field set into Unique
            if user_object.check_password(password):

                return user_object
            
            else:

                return None
        
        except:

            return None
        
    
    def get_user(self, user_id):

        try:

            return User.objects.get(id=user_id)
        
        except:

            return None