from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

from django.contrib.auth import get_user_model

def health_check(request):
    """
    Lightweight health check to signal the server is awake.
    Does not block on DB to avoid cold start timeouts.
    """
    return JsonResponse({
        "status": "healthy", 
        "service": "jewellery-marketplace-backend",
        "awake": True
    })

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('api/health/', health_check), # Ensure both match for axios.get
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/products/', include('products.urls')),
    path('api/wishlist/', include('wishlist.urls')),
    path('api/coupons/', include('coupons.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/suppliers/', include('suppliers.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
