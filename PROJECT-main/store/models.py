from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(User,null=True,blank=True,on_delete=models.SET_NULL)
    name = models.CharField(max_length=200,null=True)
    email = models.CharField(max_length=200,null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    name= models.CharField(max_length=200,null=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    image = models.ImageField(null=True,blank=True)
    primarycategory = models.CharField(max_length=200,null=True)
    secondarycategories = models.CharField(max_length=400,null=True)
    brand = models.CharField(max_length=200,null=True)
    dbid = models.CharField(max_length=200,null=True)
    #Image
    def __str__(self):
        return self.name

    
class Order(models.Model):
    customer=models.ForeignKey(Customer,on_delete=models.SET_NULL,blank=True,null=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False,null=True,blank=False)
    transaction_id = models.BigAutoField(primary_key=True)
    def __str__(self):
        return str(self.transaction_id)
    
    @property
    def getCartTotal(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.getTotal for item in orderitems])
        return total

    @property 
    def getCartItems(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total
    
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL,null=True)
    order = models.ForeignKey(Order,on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0,null=True,blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.product.name)
    
    @property
    def getTotal(self):
        return self.quantity * self.product.price

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True)
    order=models.ForeignKey(Order,on_delete=models.SET_NULL,null=True)
    postcode = models.CharField(max_length=200,null=False)
    address1 = models.CharField(max_length=200,null=False)
    address2 = models.CharField(max_length=200,null=True)
    city = models.CharField(max_length=200,null=False)
    date_added = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.postcode
    
class Reviews(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_id = models.CharField(max_length=200,null=False)
    review_rating = models.IntegerField(default = 0, null=True, blank = True)
    review_username = models.CharField(max_length=200,null=False)
    review_title = models.CharField(max_length =200,null=True)
    review_text = models.CharField(max_length=8400,null=True)
    def __str__(self):
        return self.product_id
    
