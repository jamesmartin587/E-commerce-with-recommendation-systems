from django.shortcuts import render
from .models import *
from django.http import JsonResponse
import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterUserForm
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import numpy as np
import pandas as pd
from surprise import Dataset, SVD, Reader
from collections import defaultdict
import random

# Create your views here.
def userAuth(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,complete = False)
        items = order.orderitem_set.all() 
        cartItems = order.getCartItems   
    else:
        items=[]
        order = {'getCartTotal':0,'getCartItems':0}
        cartItems = order['getCartItems']
        try:
            cart = json.loads(request.COOKIES['cart'])
        except:
            cart={}
        for i in cart:
            cartItems+=cart[i]['quantity']
            product=Product.objects.get(id=i)
            total = product.price * cart[i]['quantity']
            order['getCartTotal'] += total
            item = {
            'product':{
                'id':product.id,
                'name':product.name,
                'price':product.price,
                'image':product.image,
            },
            'quantity':cart[i]['quantity'],
            'getTotal':total,
            }
            items.append(item)
        order['getCartItems']=cartItems
    categories = Product.objects.values('primarycategory').distinct()
    context ={'items':items,'order':order,'cartItems':cartItems,'categories':categories}
    return context

def store(request):
    context=userAuth(request)
    products = Product.objects.all()
    context['products']=products
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        orderItems = OrderItem.objects.filter(order=order)
    else: 
        order = []
        for item in context['items']:
            order.append(item['product']['id']) 
        orderItems = OrderItem.objects.filter(product__in =order)
    context['recommends']=cosine_similarity_recommender(orderItems)
    print(context['recommends'])
    return render(request,'store/store.html',context )

def checkout(request):
    context =collabFiltReco(request)
    print(context['collabRec'])
    print(context['items'])
    return render(request,'store/checkout.html',context )

def cart(request):
    context=userAuth(request)
    return render(request,'store/cart.html',context )

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer,complete=False)
    orderItem,created = OrderItem.objects.get_or_create(order=order,product=product)
    if action=='add':
        orderItem.quantity +=1
        orderItem.save()
        context = userAuth(request)
        return render(request,'store/cart.html',context)
    elif action=='adds':
        orderItem.quantity+=1
    elif action=='remove':
        orderItem.quantity-=1
    orderItem.save()
    if orderItem.quantity<=0:
        orderItem.delete()
    context = userAuth(request)
    return render(request,'store/cart.html',context)

def processOrder(request):
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,complete=False)
    else:
        name= data['form']['name']
        email = data['form']['email']
        context = userAuth(request)
        items = context['items']
        customer, created = Customer.objects.get_or_create(
            email=email,
        )
        customer.name = name
        customer.save()

        order = Order.objects.create(
            customer = customer,
            complete=False,
        )
        for item in items:
            orderItem = OrderItem.objects.create(
                product = Product.objects.get(id=item['product']['id']),
                order = order,
                quantity = item['quantity'],
            )

    total = float(data['form']['total'])
    order.complete = True
    order.save()
    ShippingAddress.objects.create(customer=customer,
                                    order=order,
                                    postcode=data['shipping']['postcode'],
                                    address1=data['shipping']['address1'],
                                    address2=data['shipping']['address2'],
                                    city=data['shipping']['city'])
    return JsonResponse('Payment complete',safe=False)

def signup(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            user = authenticate(username = username, password = password)
            customer, created = Customer.objects.get_or_create(
                email=email,
            )
            customer.user = user
            customer.name = name
            customer.save()

            login(request,user)
            messages.success(request,("Registration successful"))
            return redirect('store')
        else:
            messages.success(request,("Regristation not successful"))
    else:
        form = RegisterUserForm()
    return render(request, 'store/signup.html',{'form':form,})

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password = password)
        if user is not None:
            login(request,user)
            return redirect('store')
        else:
            messages.success(request,"There was an error logging in, try again...")
            return redirect('login')
    else:
        return render(request,'store/login.html',{})
    
def logout_user(request):
    logout(request)
    messages.success(request,"Successfully logged out")
    return redirect('store')

def search(request):
    context = userAuth(request)
    products = Product.objects.all()
    context['products']=products
    if request.method =="POST":
        searched = request.POST['searchbars']
        if searched == "":
            products = Product.objects.all()
            context['products']=products
            return render(request,'store/store.html',context)
        products = Product.objects.filter(name__contains= searched)
        context['products']=products
        context.update({"searched":searched})
    return render(request, 'store/search.html',context)

def categorysearch(request):
    context = userAuth(request)
    products = Product.objects.all()
    context['products']=products
    if request.method =="POST":
        searched = request.POST['categorysearch']
        if searched == "":
            products = Product.objects.all()
            context['products']=products
            return render(request,'store/category_search.html',context)
        products = Product.objects.filter(primarycategory= searched)
        context['products']=products
        context.update({"searched":searched})
    return render(request, 'store/category_search.html',context)


def cosine_similarity_recommender(orderItems):
    products = []
    for orderItem in orderItems:
        reco_items = cosine_similarity_recommends(orderItem)
        products+=Product.objects.filter(id__in=(reco_items[1],reco_items[2],reco_items[3]))
    return list(set(products))
    


def cosine_similarity_recommends(orderItem):
    all_processed_product = text_preprocessing()
    name_processed_product = all_processed_product[0]
    primary_category_product = all_processed_product[1]
    secondary_category_product = all_processed_product[2]
    brand_category_product = all_processed_product[3]
    PV = CountVectorizer(stop_words = 'english')
    SV = CountVectorizer()
    BV = CountVectorizer()
    NV = CountVectorizer()
    name_matrix = NV.fit_transform(name_processed_product)
    primary_matrix = PV.fit_transform(primary_category_product)
    secondary_matrix = SV.fit_transform(secondary_category_product)
    brand_matrix = BV.fit_transform(brand_category_product)
    name_cosine_similarity = cosine_similarity(name_matrix)
    primary_cosine_similarity = cosine_similarity(primary_matrix)
    secondary_cosine_similarity = cosine_similarity(secondary_matrix)
    brand_cosine_similarity = cosine_similarity(brand_matrix)
    all_cosine_similarity = name_cosine_similarity + primary_cosine_similarity + secondary_cosine_similarity + brand_cosine_similarity
    id = orderItem.product_id
    orderItem_cosine = all_cosine_similarity[id-1]
    li = [] 
    for i in range(len(orderItem_cosine)):
        li.append([orderItem_cosine[i],i+1])
    li.sort()
    sortIndex = []
    for x in li:
        sortIndex.append(x[1])
    sortIndex.reverse()
    #Recommends using cosine similarity dependent on product given
    return sortIndex

def text_preprocessing():
    name_processed_products = []
    primary_processed_products = []
    secondary_processed_products = []
    brand_processed_products = []
    allProducts = Product.objects.all()
    for product in allProducts: 
        name = character_preprocessing(product.name)
        name_processed_products.append(name)
        primarycategory = character_preprocessing(product.primarycategory)
        primary_processed_products.append(primarycategory)
        secondarycategories = character_preprocessing(product.secondarycategories)
        secondary_processed_products.append(secondarycategories)
        brand = character_preprocessing(product.brand)
        brand_processed_products.append(brand)
    return [name_processed_products,primary_processed_products,secondary_processed_products,brand_processed_products]

def character_preprocessing(word):
    preprocessing_table = str.maketrans({'@':'','%':'',':':'',',':'','(':'',')':''})
    word = word.lower()
    word = word.translate(preprocessing_table)
    return word 


def get_top_n(predictions, n):
    # First map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))
    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n

def collabFiltReco(request):

    context =userAuth(request)
    review = Reviews.objects.all()
    usernames = review.values_list('review_username',flat=True).distinct()
    random_sample = random.sample(range(0,usernames.count()-1),1200)
    reader = Reader(rating_scale=(1, 5))
    distinct_username_list = list(usernames)
    sample_names = [distinct_username_list[i] for i in random_sample]
    sampled_users = review.filter(review_username__in = sample_names) 
    user_item_matrice = pd.DataFrame({'usernames':[u.review_username for u in sampled_users],'items':[i.product_id for i in sampled_users],'rating':[r.review_rating for r in sampled_users]}) 
    items = context['items']
    cim = []
    if request.user.is_authenticated:
        usersname = str(request.user.customer)
        for item in items:
            item_quantity = item.quantity
            rating = 4
            item_id = item.product.dbid
            cim.append([usersname,item_id,rating])
    else:
        usersname = "anonymous"
        print("REQUEST",context)
        for item in items:
            item_quantity = item['quantity']
            rating = 4
            item_id = item['product']['id']
            cim.append([usersname,item_id,rating])
    customer_item_matrice = pd.DataFrame(cim,columns=['usernames','items','rating'])
    user_item_matrice = pd.concat([user_item_matrice,customer_item_matrice],ignore_index=True)
    data = Dataset.load_from_df(user_item_matrice[["usernames", "items", "rating"]], reader)
    algo = SVD()
    trainset = data.build_full_trainset()
    algo.fit(trainset)
    testset = trainset.build_anti_testset()
    predictions = algo.test(testset)
    top_n = get_top_n(predictions,n=5)
    products = []
    # Print the recommended items for user
    for pid in top_n[usersname]:
        print(pid[0])
        product = Product.objects.filter(dbid=pid[0])
        print(product)
        products.append(product[0])
    context['collabRec'] = products
    return context

    

