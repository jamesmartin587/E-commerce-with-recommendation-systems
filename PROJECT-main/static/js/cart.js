var updateBtns = document.getElementsByClassName('update-cart')
for(var i=0;i<updateBtns.length;i++){
    updateBtns[i].addEventListener('click',function(){
        var productId = this.dataset.product
        var action = this.dataset.action
        console.log('productId:',productId,'action',action)
        console.log('USER',user)
        if(user==='AnonymousUser'){
            if(action=='add' || action=='adds'){
                if(cart[productId]==undefined){
                    cart[productId] = {'quantity':1}
                }
                else{
                    console.log(cart[productId]['quantity'])
                    cart[productId]['quantity']+=1
                    console.log(cart[productId]['quantity'])
                }
            }
            if(action=='remove'){
                cart[productId]['quantity']-=1
                if(cart[productId]['quantity']<=0){
                    console.log('Remove Item')
                    delete cart[productId]
                }
            }    
            document.cookie = 'cart=' + JSON.stringify(cart)+";domain=;path=/"
            location.reload()
        }else{
            console.log('user is authenticated')
            var url = '/update_item/'
            fetch(url,{
                method:'POST',
                headers:{
                    'Content-Type':'application/json',
                    'X-CSRFToken':csrftoken,
                },
                body:JSON.stringify({'productId':productId,'action':action})
            })
            .then((response)=>{
                return response.json()
            })
            .then((data)=>{
                console.log('data:', data)
            })
        }
        location.reload()
    })
}
