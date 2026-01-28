from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .forms import RegisterUserForm
from store.models import Product, Order, OrderItem, ShippingAddress, Customer, Reviews
from store.views import *
import json
from django.http import HttpRequest
from surprise import Dataset, SVD, Reader
import numpy as np
import pandas as pd
from surprise.model_selection import train_test_split
from http.cookies import SimpleCookie
# Create your tests here.
#redirect is a 302 response 
#return is a 200 response 
class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.signup_request = {'email':'test_user@email.com','name':'test_user','username':'test_user','password1':'password321',
                        'password2':'password321'}
        # self.form = RegisterUserForm(self.test_request)
        # self.form.save()
        self.customer = Customer.objects.create(
            name = 'test_name', 
            email = 'test_name@email.com'
        )
        self.product1 = Product.objects.create(
            name = 'product1',
            price = 19.99,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
        )
        self.order1 = Order.objects.create(
            customer = self.customer,
            transaction_id = 1,
        )
        self.order_item1 = OrderItem.objects.create(
            product = self.product1,
            order = self.order1,
            quantity = 2
        )
        self.product2 = Product.objects.create(
            name = 'product2',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
        )
        self.order_item2 = OrderItem.objects.create(
            product = self.product2,
            order = self.order1,
            quantity = 3
        )

        self.shipping_address1 = ShippingAddress.objects.create(
            customer = self.customer,
            order = self.order1, 
            postcode = 'postcode',
            address1 = 'address1',
            address2 = 'address2',
            city = 'city'
        )
        self.review = Reviews.objects.create(
            product_id = 'PDCTURO1',
            review_rating = 4,
            review_username = "USERNAME",
            review_title = "4 out of 5 would recommend...",
            review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
        )
    #Model Testing
    #Test 1
    #Ensures setUp is correct, and Customer model correctly updates
    def test_setUp_customer(self):
        self.assertEqual(self.customer.name, 'test_name')
        self.assertEqual(len(Customer.objects.all()),1)

    #Test 2
    #Checks Product model updates correctly
    def test_product_model(self):
        self.assertEqual(self.product1.name, 'product1')
        self.assertEqual(len(Customer.objects.all()),1)

    #Test 3
    #Checks Order model updates correctly and automatically puts complete false 
    def test_order_model(self):
        self.assertEqual(self.order1.customer, self.customer)
        self.assertEqual(len(Order.objects.all()),1) 
        self.assertEqual(self.order1.complete,False)

    #Test 4 
    #Checks OrderItem model updates correctly
    def test_order_item_model(self):
        self.assertEqual(self.order_item1.product,self.product1 )
        self.assertEqual(len(OrderItem.objects.all()),2) 

    #Test 5 
    #Checks OrderItem model property getTotal
    def test_order_item_getTotal_model(self):
        self.assertEqual(self.order_item1.getTotal, 39.98 )

    #Test 6
    #Checks properties of Order model getCartTotal and getCartItems
    def test_order_properties_model(self):
        self.assertEqual(self.order1.getCartItems, 5)
        self.assertEqual(self.order1.getCartTotal.__float__(), 70.22)

    #Test 7 
    #Checks ShippingAddress model updates correctly
    def test_shipping_address_model(self):
        self.assertEqual(self.shipping_address1.customer,self.customer )
        self.assertEqual(len(ShippingAddress.objects.all()),1)

    def test_Review(self):
        self.assertEqual(self.review.product_id, "PDCTURO1")
        self.assertEqual(len(Reviews.objects.all()),1)
    #Views testing 
    #Test 1 
    #Tests the store view gets the correct template store.html
    def test_store_GET(self):
        response = self.client.get(reverse('store'))

        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/store.html')
    
    #Test 2 
    #Tests the login view gets the correct template login.html
    def test_login_GET(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/login.html')
    
    #Test 3 
    #Tests existing user with correct credentials can successful be logged in 
    def test_login_correct_POST(self):
        form = RegisterUserForm(self.signup_request)
        form.save()
        user = authenticate(username='test_user',password='password321')
        self.customer2 = Customer.objects.create(
            user = user,
            name = 'test_name', 
            email = 'test_name@email.com'
        )

        test_login_request = {'username':'test_user','password':'password321'}
        response = self.client.post(reverse('login'),test_login_request)
        self.assertEqual(response.status_code,302)
        self.assertRedirects(response,'/')
    
    #Test 4 
    #Tests existing user with incorrect credentials cannot successful login 
    def test_login_incorrect_POST(self):
        test_login_request = {'username':'test_false_user','password':'password321'}
        response = self.client.post(reverse('login'),test_login_request)
        self.assertEqual(response.status_code,302)
        self.assertRedirects(response,'/login_user/')

    #Test 5 
    #Tests the login view gets the correct template login.html
    def test_login_user_GET(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/login.html')

    #Test 6 
    #Tests the logout view redirects to store
    def test_logout_user_GET(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code,302)
        self.assertRedirects(response,'/')
  
    #Test 7
    #Tests the signup view gets the correct template signup.html
    def test_signup_GET(self):
        response = self.client.get(reverse('signup'))

        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/signup.html')

    #Test 8 
    #Tests signup for corret credentials work 
    def test_signup_correct_POST(self):
        response = self.client.post(reverse('signup'),self.signup_request)
        
        self.assertEqual(response.status_code,302)
        self.assertRedirects(response,'/')

    #Test 9 
    #Tests duplicate usernames cannot be entered, the correct error message is returned in context
    def test_signup_duplicate_POST(self):
        form = RegisterUserForm(self.signup_request)
        form.save()
        incorrect_signup_request = {'email':'test_user@email.com','name':'test_user','username':'test_user','password1':'password321',
                        'password2':'password321'}           
        response = self.client.post(reverse('signup'),incorrect_signup_request)     
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/signup.html')
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, "success")
        self.assertTrue("Regristation not successful" in message.message)

    #Test 10
    #Tests the cart view gets the correct template cart.html
    def test_cart_GET(self):
        response = self.client.get(reverse('cart'))

        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/cart.html')

    #Test 11 
    #Tests the checkout view gets the correct template checkout.html
    def test_checkout_GET(self):
        for i in range(0,1200):
            Reviews.objects.create(
                product_id = 'PDCTURO1',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/checkout.html')

    #Test 12
    #Tests category search view gets the correct template category_search.html
    def test_category_search_GET(self):
        response = self.client.get(reverse('category_search'))
         
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/category_search.html')

    #Test 13
    #Tests category_search view posts the correct category when given a category
    def test_category_search_POST(self):
        product3 = Product.objects.create(
            name = 'product3',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category2',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand'
        )
        request = {'categorysearch':'category'}
        response = self.client.post(reverse('category_search'),request)
         
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/category_search.html')
        product = list(response.context.get('products'))
        self.assertEqual(len(product), 2)

    #Test 14
    #Tests search view gets the correct template search.html
    def test_search_GET(self):
        response = self.client.get(reverse('search'))
         
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/search.html')

    #Test 15
    #Tests search view posts the correct search results when given a search
    def test_search_POST(self):
        request = {'searchbars':'product'}
        response = self.client.post(reverse('search'),request)
         
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'store/search.html')
        product = list(response.context.get('products'))
        self.assertEqual(len(product), 2)

    #Test 15
    #Tests search view posts when empty search results given
    def test_search_POST(self):
        request = {'searchbars':''}
        response = self.client.post(reverse('search'),request)
         
        self.assertEqual(response.status_code,200)
        #goes back to the home page
        self.assertTemplateUsed(response, 'store/store.html')
        product = list(response.context.get('products'))
        self.assertEqual(len(product), 2)

    
    #Test 16  
    #Tests cart to add an item and check that cartItems get its quantities 
    def test_cart_add(self):
        form = RegisterUserForm(self.signup_request)
        form.save()
        user = authenticate(username='test_user',password='password321')
        self.customer2 = Customer.objects.create(
            user = user,
            name = 'test_name', 
            email = 'test_name@email.com'
        )
        test_login_request = {'username':'test_user','password':'password321'}
        test_update_item_request = {"productId":"2","action":"add"}
        self.client.post(reverse('login'),test_login_request)
        self.client.post(reverse('update_item'),json.dumps(test_update_item_request),content_type='application/json')
        response = self.client.get(reverse('cart'))
        self.assertTemplateUsed(response, 'store/cart.html')
        self.assertEqual(response.context['cartItems'],1)
    
    #Test 17
    #Tests cart properly removes an item from basket 
    def test_cart_remove(self):
        form = RegisterUserForm(self.signup_request)
        form.save()
        user = authenticate(username='test_user',password='password321')
        self.customer2 = Customer.objects.create(
            user = user,
            name = 'test_name', 
            email = 'test_name@email.com'
        )
        test_login_request = {'username':'test_user','password':'password321'}
        test_update_item_request = {"productId":"2","action":"add"}
        self.client.post(reverse('login'),test_login_request)
        self.client.post(reverse('update_item'),json.dumps(test_update_item_request),content_type='application/json')
        test_update_item_request = {"productId":"2","action":"remove"}
        self.client.post(reverse('update_item'),json.dumps(test_update_item_request),content_type='application/json')
        response = self.client.get(reverse('cart'))
        self.assertTemplateUsed(response, 'store/cart.html')
        self.assertEqual(response.context['cartItems'],0)

    #Test 18
    #Tests cart properly removes an item from basket 
    def test_cart_adds(self):
        form = RegisterUserForm(self.signup_request)
        form.save()
        user = authenticate(username='test_user',password='password321')
        self.customer2 = Customer.objects.create(
            user = user,
            name = 'test_name', 
            email = 'test_name@email.com'
        )
        test_login_request = {'username':'test_user','password':'password321'}
        test_update_item_request = {"productId":"2","action":"adds"}
        self.client.post(reverse('login'),test_login_request)
        self.client.post(reverse('update_item'),json.dumps(test_update_item_request),content_type='application/json')
        test_update_item_request = {"productId":"2","action":"remove"}
        self.client.post(reverse('update_item'),json.dumps(test_update_item_request),content_type='application/json')
        response = self.client.get(reverse('cart'))
        self.assertTemplateUsed(response, 'store/cart.html')
        self.assertEqual(response.context['cartItems'],0)
    
from surprise import Dataset, SVD, Reader
class UnitTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_request = {'email':'test_user@email.com','name':'test_user','username':'test_user','password1':'password321',
                        'password2':'password321'}

        self.customer = Customer.objects.create(
            name = 'test_user', 
            email = 'test_user@email.com'
        )
        self.product1 = Product.objects.create(
            name = 'product1',
            price = 19.99,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO1',
        )
        self.product2 = Product.objects.create(
            name = 'product2',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO2',
        )
        self.order1 = Order.objects.create(
            customer = self.customer,
            transaction_id = 1,
        )
        self.order_item1 = OrderItem.objects.create(
            product = self.product1,
            order = self.order1,
            quantity = 2
        )
    #Test 1 
    #Testing Content-based Filtering Character Preprocessing
    def test_Character_Preprocessing(self):
        processed_word = character_preprocessing("@h%e:l,l(o)")
        self.assertEqual(processed_word,"hello")

    #Test 2
    #Testing Content-based filtering text preprocessing to give a matrix of separate features in word format
    def test_text_Preprocessing(self):
        self.assertEqual(text_preprocessing(),[['product1','product2'],['category','category'],['secondarycategory1 secondarycategory2','secondarycategory1 secondarycategory2'],['brand','brand']])

    #Test 3 
    #Testing cosine_similarity_recommends method
    def test_cosine_similarity_recommends(self):
        self.assertEqual(cosine_similarity_recommends(self.order_item1),[1,2])                   
   
    #Test 4 
    #Testing cosine_similarity_recommender method
    def test_cosine_similarity_recommender(self):
        orderItems = OrderItem.objects.filter(order=self.order1)
        product3 = Product.objects.create(
            name = 'product3',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category2',
            secondarycategories = 'secondarycategory, newcategories',
            brand = 'differ',
        )
        product4 = Product.objects.create(
            name = 'product2',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
        )
        self.assertEqual(cosine_similarity_recommender(orderItems),[self.product2,product3,product4])
    
    #Test 5
    #Collaborative filtering 
    #Tests get_top_n method returns top 10 values from a predictions dictionary
    def test_get_top_n(self):
        user_item_matrice = pd.DataFrame({'usernames':['username1','username1','username1','username2','username2','username3','username3'],'items':[1,2,3,2,1,3,1],'rating':[1,4,5,3,2,5,2]}) 
        algo = SVD()
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(user_item_matrice[["usernames", "items", "rating"]], reader)
        trainset = data.build_full_trainset()
        algo.fit(trainset)
        testset = trainset.build_anti_testset()
        predictions = algo.test(testset)
        self.assertEqual(len(get_top_n(predictions,5)),2)

    #Test 6 
    #Tests Authenticated Users usage of collaborative filtering system 
    def test_user_auth_collab(self):
        form = RegisterUserForm(self.signup_request)
        form.save()
        user = authenticate(username='test_user',password='password321')    
        self.customer2 = Customer.objects.create(
            user = user,
            name = 'test_name', 
            email = 'test_name@email.com'
        )
        test_login_request = {'username':'test_user','password':'password321'}
        self.client.post(reverse('login'),test_login_request)
        test_update_item_request = {"productId":"2","action":"adds"}
        self.client.post(reverse('update_item'),json.dumps(test_update_item_request),content_type='application/json')
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO1',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO2',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO3',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO4',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO5',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        self.product3 = Product.objects.create(
            name = 'product3',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO3',
        )
        self.product4 = Product.objects.create(
            name = 'product4',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO4',
        )
        self.product5 = Product.objects.create(
            name = 'product5',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO5',
        )
        response = self.client.get(reverse('checkout'))
        self.assertEqual(len(response.context['collabRec']),4)
    
    #Test 7
    #Tests anonymous users usage of collaborative filtering system 
    def test_anonymous_user_collab(self):
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO1',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO2',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO3',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO4',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO5',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        self.product3 = Product.objects.create(
            name = 'product3',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO3',
        )
        self.product4 = Product.objects.create(
            name = 'product4',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO4',
        )
        self.product5 = Product.objects.create(
            name = 'product5',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO5',
        )
        response = self.client.get(reverse('checkout'))
        self.assertEqual(len(response.context['collabRec']),0)
        self.assertTrue(response.context['user'].__str__() =="AnonymousUser")

    #Test 8 
    #TEST case for collaborative filtering if no items are in the users basket
    def test_empty_basket_collab(self):
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO1',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO2',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO3',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO4',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        for i in range(0,1201):
            Reviews.objects.create(
                product_id = 'PDCTURO5',
                review_rating = 4,
                review_username = "USERNAME"+str(i),
                review_title = "4 out of 5 would recommend...",
                review_text = "4 out of 5 would recommend for all ages but the only dissatisfaction is this."
            ) 
        self.product3 = Product.objects.create(
            name = 'product3',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO3',
        )
        self.product4 = Product.objects.create(
            name = 'product4',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO4',
        )
        self.product5 = Product.objects.create(
            name = 'product5',
            price = 10.08,
            image = 'https://www.webfx.com/wp-content/uploads/2021/10/generic-image-placeholder.png',
            primarycategory = 'category',
            secondarycategories = 'secondarycategory1, secondarycategory2',
            brand = 'brand',
            dbid = 'PDCTURO5',
        )
        response = self.client.get(reverse('checkout'))
        self.assertEqual(len(response.context['collabRec']),0)