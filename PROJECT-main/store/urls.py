
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns=[
    path('',views.store,name="store"),
    path('cart/',views.cart,name="cart"),
    path('checkout/',views.checkout,name="checkout"),
    path('update_item/',views.updateItem,name="update_item"),
    path('process_order/',views.processOrder,name="process_order"),
    path('login_user/',views.login_user,name="login"),
    path('signup/',views.signup,name="signup"),
    path('logout_user/',views.logout_user,name="logout"),
    path('search/',views.search, name="search"),
    path('category_search/',views.categorysearch,name="category_search"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)