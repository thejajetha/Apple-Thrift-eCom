from django.contrib import admin
from store.models import User,Category,Product,ProductVariant,Color,Storage,ProductImage
# Register your models here.

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(Color)
admin.site.register(Storage)
admin.site.register(ProductImage)


