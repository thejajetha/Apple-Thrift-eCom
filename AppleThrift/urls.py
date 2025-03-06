"""
URL configuration for AppleThrift project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from store import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/signin/')),

    path('admin/', admin.site.urls),
    path('signup/',views.SignUpView.as_view(),name='signup'),
    path("otp/verify/",views.OtpVerifyView.as_view(),name="otp-verify"),
    path("signin/",views.SignInView.as_view(),name="signin"),
    path('signout/',views.SignOutView.as_view(),name='signout'), 
    path("index/",views.IndexView.as_view(),name="index"),
    path('product/<int:pk>/',views.ProductDetailView.as_view(),name='product-detail'),
    path('product/add/cartorwishlist/',views.AddToCartOrWishlistView.as_view(),name='add-to-cart-wishlist'),
    path('cart/summary/',views.CartSummaryView.as_view(),name='cart-summary'),
    path('wishlist/summary/',views.WishlistSummaryView.as_view(),name='wishlist-summary'),
    path('cart/<int:pk>/remove/',views.CartItemDeleteView.as_view(),name="cart-item-delete"),
    path('wishlist/<int:pk>/remove/',views.WishlistItemDeleteView.as_view(),name='wishlist-item-delete'),
    path("place/order/",views.OrderCreateView.as_view(),name='order-create'),
    path('order/summary/',views.OrderSummaryView.as_view(),name='order-summary'),
    path('payment/verify/',views.PaymentVerificationView.as_view(),name='payment-verify'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 