from django.shortcuts import render,redirect
from django.views.generic import View
from store.forms import SignUpForm,OtpVerifyForm,SignInForm,OrderForm
from store.models import User
from twilio.rest import Client
from decouple import config
from django.contrib.auth import authenticate,login,logout
from store.models import Product,Cart,ProductVariant,Color,OrderItem,Order,Category,Wishlist
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from store.decorators import signin_required

# Create your views here.

twilio_acc_sid=config("TWILIO_ACC_SID")

twilio_acc_secret=config("TWILIO_ACC_SECRET")

twilio_phone_number=config("TWILIO_PHONE_NUMBER")

my_phone_number=config('MY_PHONE_NUMBER')

rzp_key_id=config("RZP_KEY_ID")

rzp_key_secret=config("RZP_KEY_SECRET")

def sent_otp_phone(user_object):

    user_object.generate_otp()

    account_sid = twilio_acc_sid
    auth_token = twilio_acc_secret
    client = Client(account_sid, auth_token)
    message = client.messages.create(
    from_=twilio_phone_number,
    body=user_object.otp,
    to=my_phone_number
    )
    print(message.sid)

class SignUpView(View):

    template_name="signup.html"

    form_class=SignUpForm

    def get(self,request,*args,**kwrags):

        form_instance=self.form_class()

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):

        form_instance=self.form_class(request.POST)

        if form_instance.is_valid():

            user_instance=form_instance.save(commit=False)

            user_instance.is_active=False

            user_instance.save()

            sent_otp_phone(user_instance)

            return redirect("otp-verify")
        
        else:

            return render(request,self.template_name,{"form":form_instance})
        
class OtpVerifyView(View):

    template_name="otpverify.html"

    form_class=OtpVerifyForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):

        otp_instance=request.POST.get("otp")

        try:
            
            user_object=User.objects.get(otp=otp_instance)

            user_object.is_active=True

            user_object.is_verified=True

            user_object.otp=None

            user_object.save()

            return redirect("signin")

        except:

            print("failed to verify")

            return redirect("otp-verify")

class SignInView(View):

    template_name="signin.html"

    form_class=SignInForm

    def get(self,request,*args,**kwargs):

        form_instance=self.form_class()

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):

        form_instance=self.form_class(request.POST)

        if form_instance.is_valid():

            uname=form_instance.cleaned_data.get("username")

            pwd=form_instance.cleaned_data.get("password")

            user_object=authenticate(request,username=uname,password=pwd)

            if user_object:

                login(request,user_object)

                return redirect("index")

        return render(request,self.template_name,{"form":form_instance})
    
@method_decorator(signin_required,name="dispatch") 
class SignOutView(View):

    def get(self,request,*args,**kwargs):

        logout(request)

        return redirect("signin")
    
@method_decorator(signin_required,name="dispatch") 
class IndexView(View):

    template_name = "index.html"

    def get(self, request, *args, **kwargs):

        products = Product.objects.all()

        search_query = request.GET.get("search", "")

        category_filter = request.GET.get("category", "")

        if search_query:
            products = products.filter(name__icontains=search_query)

        if category_filter:
            products = products.filter(categories__name__iexact=category_filter)

        categories = Category.objects.all()  # Fetch all categories

        return render(request, self.template_name, {"products": products, "categories": categories})

@method_decorator(signin_required,name="dispatch") 
class ProductDetailView(View):

    template_name="product_detail.html"

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        qs=Product.objects.get(id=id)

        return render(request,self.template_name,{'product':qs})
    
@method_decorator(signin_required,name="dispatch") 
class AddToCartOrWishlistView(View):

    def post(self,request,*args,**kwargs):

        action=request.POST.get("action")

        product_variant_id=request.POST.get("variant")
        product_variant_instance=ProductVariant.objects.get(id=product_variant_id)

        color_id=request.POST.get("color")
        color_instance=Color.objects.get(id=color_id)

        qty=request.POST.get("quantity")

        if action=="cart":

            Cart.objects.create(
                product_variant=product_variant_instance,
                color=color_instance,
                quantity=qty,
                user=request.user)

            return redirect("index")
        
        if action=="wishlist":

            Wishlist.objects.create(
                user=request.user,
                product_variant=product_variant_instance,
                color=color_instance
            )

            return redirect('index')

@method_decorator(signin_required,name="dispatch")  
class CartSummaryView(View):

    template_name='cart_summary.html'

    def get(self,request,*args,**kwargs):

        qs=Cart.objects.filter(user=request.user,is_order_placed=False)

        basket_total=sum([c.item_total() for c in qs])

        return render(request,self.template_name,{"cart":qs,"basket_total":basket_total})

@method_decorator(signin_required,name="dispatch")   
class WishlistSummaryView(View):

    template_name="wishlist_summary.html"

    def get(self,request,*args,**kwargs):

        qs=Wishlist.objects.filter(user=request.user)

        return render(request,self.template_name,{"wishlist":qs})

@method_decorator(signin_required,name="dispatch") 
class CartItemDeleteView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        Cart.objects.get(id=id).delete()

        return redirect("cart-summary")

@method_decorator(signin_required,name="dispatch") 
class WishlistItemDeleteView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get('pk')

        Wishlist.objects.get(id=id).delete()

        return redirect("wishlist-summary")        

@method_decorator(signin_required,name="dispatch")    
class OrderCreateView(View):
     
     template_name='order_create.html'

     form_class=OrderForm

     def get(self,request,*args,**kwargs):
         
         form_instance=self.form_class()

         cart_items=Cart.objects.filter(user=request.user,is_order_placed=False)

         basket_total=sum([c.item_total() for c in cart_items])

         return render(request,self.template_name,{"form":form_instance,"cart_items":cart_items,"basket_total":basket_total})
     
     def post(self,request,*args,**kwargs):
         
         form_instance=self.form_class(request.POST)

         if form_instance.is_valid():
             
             form_instance.instance.customer=request.user

             order_object=form_instance.save() 

             cart_object=Cart.objects.filter(user=request.user,is_order_placed=False)

             for ci in cart_object:
                 
                 OrderItem.objects.create(
                    order=order_object,
                    product_variant=ci.product_variant,
                    quantity=ci.quantity,
                    color=ci.color,
                    price=ci.product_variant.price
                 )

                 ci.is_order_placed=True

                 ci.save()

             payment_method=request.POST.get('payment_method')

             if payment_method=='ONLINE':
                 
                client = razorpay.Client(auth=(rzp_key_id, rzp_key_secret))

                sub_total=order_object.order_total()*100        

                data = { "amount": sub_total, "currency": "INR", "receipt": "order_rcptid_11" }

                payment = client.order.create(data=data)    
                # payment var have all the payment details id,reciept etc

                rzp_id=payment.get('id')  #id from payment assigned to rzp_id

                order_object.rzp_order_id=rzp_id

                order_object.save()

                context={
                    'key_id':rzp_key_id,
                    'amount':sub_total,
                    'order_rzp_id':order_object.rzp_order_id,
                    "currency":'INR'

                }

                return render(request,'payment.html',context)

             return redirect("index")
         
@method_decorator(signin_required,name="dispatch") 
class OrderSummaryView(View):

    template_name="order_summary.html"

    def get(self,request,*args,**kwargs):

        qs=Order.objects.filter(customer=request.user).order_by("-created_date")

        return render(request,self.template_name,{'orders':qs})
    
@method_decorator(csrf_exempt,name="dispatch")     #csrf_exempt- this used to work post without csrf_token
class PaymentVerificationView(View):               

    def post(self,request,*args,**kwargs):

        print(request.POST)                       
        #req.post have all the details of payment 
        # <QueryDict: {'razorpay_payment_id': ['pay_Q1yXxlrem44jxu'], 'razorpay_order_id': ['order_Q1yXmwDcWLIoxS'], 
        # razorpay_signature': ['80d319a0d1df95658fef0e88bd061049d1a3587c6b789c550a79bee9f71429ab']}>

        client = razorpay.Client(auth=(rzp_key_id, rzp_key_secret))

        try:

            client.utility.verify_payment_signature(request.POST)

            razorpay_order_id=request.POST.get("razorpay_order_id")

            Order.objects.filter(rzp_order_id=razorpay_order_id).update(is_paid=True)

        except:

            print("failed  signature verfication")

        return redirect('order-summary')   #redirect to our callback url 



     
    






