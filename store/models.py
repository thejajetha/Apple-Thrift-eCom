from django.db import models
from django.contrib.auth.models import AbstractUser
from random import randint
# from django.utils import timezone


# Create your models here.
class User(AbstractUser):

    phone = models.CharField(max_length=15, unique=True)

    is_verified = models.BooleanField(default=False)

    otp = models.CharField(max_length=10,null=True)

    def generate_otp(self):

        self.otp=str(randint(1000,9999))

        self.save() 




# Reusable BaseModel
class BaseModel(models.Model):

    created_date = models.DateTimeField(auto_now_add=True)

    updated_date = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True 



class Storage(BaseModel):

    storage = models.CharField(max_length=20,unique=True)

    def __str__(self):        
        return self.storage
    

class Color(BaseModel):

    name=models.CharField(max_length=70,unique=True)

    def __str__(self):
        return self.name
    

class Category(BaseModel):

    name=models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.name



class Product(BaseModel):

    name = models.CharField(max_length=100)
 
    description = models.TextField()

    image = models.ImageField(upload_to="product_images", null=True, blank=True)  

    categories = models.ManyToManyField(Category)

    colors = models.ManyToManyField(Color)

    def __str__(self):
        return f"{self.name}" 
    

class ProductImage(BaseModel):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")

    image = models.ImageField(upload_to="product_images")

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(BaseModel):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    storage = models.ForeignKey(Storage,on_delete=models.CASCADE)

    price = models.FloatField()

    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.storage.storage} - MRP{self.price}"
    

class Review(BaseModel):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    rating = models.PositiveIntegerField()

    comment = models.TextField()
    

class Cart(BaseModel):

    product_variant=models.ForeignKey(ProductVariant,on_delete=models.CASCADE)

    color = models.ForeignKey(Color,on_delete=models.CASCADE)

    user = models.ForeignKey(User,on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()

    is_order_placed = models.BooleanField(default=False)

    def item_total(self):

        return self.quantity*self.product_variant.price
    

class Wishlist(BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")

    product_variant=models.ForeignKey(ProductVariant,on_delete=models.CASCADE)

    color = models.ForeignKey(Color,on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "product_variant", "color")  #Ensures a user cannot add the same item multiple times.

    def __str__(self):
        return f"{self.user.username} - {self.product_variant.product.name} ({self.color.name})"



class Order(BaseModel):

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    address = models.TextField(null=False, blank=False)

    phone = models.CharField(max_length=20, null=False, blank=False)

    PAYMENT_OPTIONS = (
        ("COD", "Cash on Delivery"),
        ("ONLINE", "Online Payment"),
    )

    payment_method = models.CharField(max_length=30, choices=PAYMENT_OPTIONS, default="COD")

    rzp_order_id = models.CharField(max_length=100, null=True)

    is_paid = models.BooleanField(default=False)

    def order_total(self):

        order_items=self.orderitems.all()

        total=0

        if order_items:

            total=sum([oi.item_total() for oi in order_items])

        return total

            

class OrderItem(BaseModel):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderitems")

    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)

    color = models.ForeignKey(Color,on_delete=models.CASCADE)

    price = models.FloatField()

    def item_total(self):

        return self.quantity*self.price



