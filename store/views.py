from django.shortcuts import render,redirect,get_object_or_404
from django.views.generic import View
from store.forms import SignUpForm,OtpVerifyForm,SignInForm,OrderForm,ReviewForm
from store.models import User
# from twilio.rest import Client
from django.core.mail import send_mail
from decouple import config
from django.contrib.auth import authenticate,login,logout
from store.models import Product,Cart,ProductVariant,Color,OrderItem,Order,Category,Wishlist,Review
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from store.decorators import signin_required
from django.contrib import messages


# Create your views here.

# twilio_acc_sid=config("TWILIO_ACC_SID")

# twilio_acc_secret=config("TWILIO_ACC_SECRET")

# twilio_phone_number=config("TWILIO_PHONE_NUMBER")

# my_phone_number=config('MY_PHONE_NUMBER')

rzp_key_id=config("RZP_KEY_ID")

rzp_key_secret=config("RZP_KEY_SECRET")

# def sent_otp_phone(user_object):

#     user_object.generate_otp()

#     account_sid = twilio_acc_sid
#     auth_token = twilio_acc_secret
#     client = Client(account_sid, auth_token)
#     message = client.messages.create(
#     from_=twilio_phone_number,
#     body=user_object.otp,
#     to=my_phone_number
#     )
#     print(message.sid)

def send_otp_email(user_object):
    user_object.generate_otp()
    subject = "Your OTP for Account Verification"
    message = f"Hello {user_object.username},\n\nYour OTP for verifying your email is: {user_object.otp}\n\nThank you!"
    from_email = None  # Will use DEFAULT_FROM_EMAIL
    recipient_list = [user_object.email]
    
    send_mail(subject, message, from_email, recipient_list)


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

            send_otp_email(user_instance)

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

        qs=get_object_or_404(Product,id=id)

        reviews=Review.objects.filter(product=qs).order_by("-created_date")

        return render(request,self.template_name,{'product':qs,"reviews":reviews})
    
@method_decorator(signin_required,name="dispatch") 
class AddToCartOrWishlistView(View):

    def post(self,request,*args,**kwargs):

        action=request.POST.get("action")

        product_variant_id=request.POST.get("variant")

        color_id=request.POST.get("color")

        qty=int(request.POST.get("quantity"))

        if not product_variant_id or not color_id:

            messages.error(request, "Please select a product variant and color.")
            
            return redirect(request.META.get("HTTP_REFERER", "index"))

        product_variant_instance=get_object_or_404(ProductVariant,id=product_variant_id)
        color_instance=get_object_or_404(Color,id=color_id)

        if action=="cart":

            existing_item=Cart.objects.filter(
                user=request.user,
                product_variant=product_variant_instance,
                color=color_instance,
                is_order_placed=False
                ).first()
            
            if existing_item:
                existing_item.quantity+=qty
                existing_item.save()
            
            else:
                Cart.objects.create(
                product_variant=product_variant_instance,
                color=color_instance,
                quantity=qty,
                user=request.user
                )


            return redirect("index")
        
        if action=="wishlist":

            existing_item=Wishlist.objects.filter(
                user=request.user,
                product_variant=product_variant_instance,
                color=color_instance
            ).exists()

            if not existing_item:

                Wishlist.objects.create(
                user=request.user,
                product_variant=product_variant_instance,
                color=color_instance,
                )

            else:

                print("Item already exists in wishlist")

            return redirect('wishlist-summary')

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
class ReviewCreateView(View):

    def post(self, request, *args, **kwargs):

        id = kwargs.get("pk")
        product = get_object_or_404(Product, id=id)
        form_instance=ReviewForm(request.POST)

        has_purchased = OrderItem.objects.filter(           # Check if the user has purchased the product
            order__customer=request.user,
            product_variant__product=product
        ).exists()

        if not has_purchased:
            messages.error(request, "You must purchase this product before leaving a review.")
            return redirect("product-detail",pk=product.id)

        if form_instance.is_valid():
            existing_review = Review.objects.filter(user=request.user, product=product).exists()

            if existing_review:
                messages.error(request, "You have already reviewed this product.")
            else:
                review = form_instance.save(commit=False)
                review.user = request.user
                review.product = product
                review.save()
                messages.success(request, "Review submitted successfully.")

        return redirect("product-detail",pk=product.id)

@method_decorator(signin_required,name="dispatch")    
class OrderCreateView(View):
     
     template_name='order_create.html'

     form_class=OrderForm

     COD_LIMIT=100000

     def get(self,request,*args,**kwargs):
         
         cart_items=Cart.objects.filter(user=request.user,is_order_placed=False)

         basket_total=sum([c.item_total() for c in cart_items])

         last_order = Order.objects.filter(customer=request.user).order_by('-created_date').first()
         initial_data = {}
         if last_order:
            initial_data['address'] = last_order.address
            initial_data['phone'] = last_order.phone

         form_instance = self.form_class(initial=initial_data)

         return render(request,self.template_name,{"form":form_instance,"cart_items":cart_items,"basket_total":basket_total})
     
     def post(self,request,*args,**kwargs):
         
         form_instance=self.form_class(request.POST)

         if form_instance.is_valid():
             
             form_instance.instance.customer=request.user

             cart_object=Cart.objects.filter(user=request.user,is_order_placed=False)

             basket_total = sum([c.item_total() for c in cart_object])

             payment_method=request.POST.get('payment_method')

             if payment_method == 'COD' and basket_total > self.COD_LIMIT:

                messages.error(request, f"COD is not available for orders above ₹{self.COD_LIMIT}.Please select an online payment method.")

                return redirect('order-create') 

             order_object=form_instance.save() 

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


     
    






