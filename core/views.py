from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count, Avg
from taggit.models import Tag
from core.models import Product, Category, Tags, Vendor, CartOrder, CartOrderItems, ProductImages, ProductReview, Wishlist, Address
from userauths.models import ContactUs, Profile
from core.forms import ProductReviewForm
from django.template.loader import render_to_string
from django.contrib import messages

from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth.decorators import login_required

from django.core import serializers

def index(request):
    products = Product.objects.filter(product_status = "published", featured = True)
    
    context = {
        "products": products
    }

    return render(request, 'core/index.html', context)

def product_list_view(request):
    products = Product.objects.filter(product_status = "published")
    
    context = {
        "products": products
    }

    return render(request, 'core/product-list.html', context)

def category_list_view(request):
    categories = Category.objects.all()

    context = {
        "categories": categories
    }

    return render(request, 'core/category-list.html', context)

def category_product_list_view(request, cid):
    category = Category.objects.get(cid = cid)
    products = Product.objects.filter(product_status = "published", category = category)

    context = {
        "category": category,
        "products": products,
    }
    return render(request, 'core/category-product-list.html', context)

def vendor_list_view(request):
    vendors = Vendor.objects.all()
    context = {
        "vendors": vendors,
    }
    return render(request, 'core/vendor-list.html', context)

def vendor_detail_view(request, vid):
    vendor = Vendor.objects.get(vid = vid)
    products = Product.objects.filter(product_status = "published", vendor = vendor)
    
    context = {
        "vendor": vendor,
        "products": products,
    }
    return render(request, 'core/vendor-detail.html', context)

def product_detail_view(request, pid):
    product = Product.objects.get(pid = pid)
    products = Product.objects.filter(category = product.category).exclude(pid = pid)

    # Getting all review
    reviews = ProductReview.objects.filter(product = product).order_by("-date")

    # Getting average review
    average_rating = ProductReview.objects.filter(product = product).aggregate(rating = Avg('rating'))

    # Product Review form
    review_form = ProductReviewForm()

    make_review = True 

    if request.user.is_authenticated:
        address = Address.objects.get(status=True, user=request.user)
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()

        if user_review_count > 0:
            make_review = False
    
    p_image = product.p_images.all()
    
    context = {
        "p": product,
        "make_review": make_review,
        "review_form": review_form,
        "p_image": p_image,
        "average_rating": average_rating,
        "reviews": reviews,
        "products": products,
    }
    return render(request, 'core/product-detail.html', context)

def tag_list(request, tag_slug=None):
    products = Product.objects.filter(product_status="published").order_by("id")
    tag = None 

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        "products": products,
        "tag": tag
    }

    return render(request, "core/tag.html", context)

def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user 

    review = ProductReview.objects.create(
        user = user,
        product = product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg("rating"))

    return JsonResponse(
       {
        'bool': True,
        'context': context,
        'average_reviews': average_reviews
       }
    )

def search_view(request):
    query = request.GET.get("q")  # Lấy từ khóa tìm kiếm từ tham số 'q' trong URL.

    # Thực hiện truy vấn cơ sở dữ liệu để tìm các sản phẩm có tiêu đề chứa từ khóa tìm kiếm.
    products = Product.objects.filter(title__icontains=query).order_by("-date")

    context = {
        "products": products,
        "query": query,
    }
    return render(request, "core/search.html", context)

def filter_products(request):
    categories = request.GET.getlist("category[]")
    vendors = request.GET.getlist("vendor[]")

    min_price = request.GET['min_price']
    max_price = request.GET['max_price']

    products = Product.objects.filter(product_status="published").order_by("-id").distinct()

    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)

    if len(categories) > 0:
        products = products.filter(category__id__in=categories).distinct() 
    
    if len(vendors) > 0:
        products = products.filter(vendor__id__in=vendors).distinct() 
        
    data = render_to_string("core/async/product-list.html", {"products": products})
    
    return JsonResponse({"data": data})

def add_to_cart(request):
    # Khởi tạo 1 dict rỗng để lưu trữ thông tin sản phẩm người dùng muốn thêm vào giỏ hàng
    cart_product = {}

    # Lấy ra thông tin sản phẩm từ request và lưu vào dict cart_product 
    # với key là id của sp
    # value là một dict chứa các thông tin như bên dưới:
    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }
    # Kiểm tra nếu giỏ hàng (cart_data_obj) đã tồn tại trong session.
    if 'cart_data_obj' in request.session:
        # Nếu sản phẩm đã có trong giỏ hàng, cập nhật số lượng của sản phẩm đó bằng số lượng mới.
        if str(request.GET['id']) in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        # Nếu sản phẩm chưa có trong giỏ hàng, thêm sản phẩm mới vào giỏ hàng bằng cách cập nhật cart_data với cart_product.
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data
    # Nếu cart_data_obj chưa tồn tại trong session, khởi tạo nó với thông tin sản phẩm hiện tại.
    else:
        request.session['cart_data_obj'] = cart_product
    # Trả về phản hồi JSON chứa thông tin giỏ hàng (cart_data_obj) và tổng số mục trong giỏ hàng.
    return JsonResponse({"data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj'])})

def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
        return render(request, "core/cart.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 
                                                  'cart_total_amount':cart_total_amount})
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")


def delete_item_from_cart(request):
    # Lấy product_id của sản phẩm cần xóa từ truy vấn của request GET.
    product_id = str(request.GET['id'])
    
    # Kiểm tra xem giỏ hàng ('cart_data_obj') có tồn tại trong session hay không.
    if 'cart_data_obj' in request.session:
        # Nếu sản phẩm với product_id đó tồn tại trong giỏ hàng,
        # tiến hành xóa nó khỏi giỏ hàng.
        if product_id in request.session['cart_data_obj']:
                    
            # Lấy dữ liệu giỏ hàng hiện tại từ session.
            cart_data = request.session['cart_data_obj']

            # Xóa sản phẩm khỏi giỏ hàng.
            del request.session['cart_data_obj'][product_id]

            # Cập nhật lại giỏ hàng trong session sau khi đã xóa sản phẩm.
            request.session['cart_data_obj'] = cart_data
    
    # Khởi tạo biến để tính tổng đơn hàng của giỏ hàng.
    cart_total_amount = 0

    # Kiểm tra lại xem giỏ hàng có tồn tại trong session sau khi xóa sản phẩm.
    if 'cart_data_obj' in request.session:
        # Duyệt qua từng sản phẩm trong giỏ hàng để tính tổng đơn hàng.
        for p_id, item in request.session['cart_data_obj'].items():
            # Tính tổng đơn hàng bằng cách nhân số lượng (qty) với giá (price) của từng sản phẩm,
            # sau đó cộng dồn vào biến cart_total_amount.
            cart_total_amount += int(item['qty']) * float(item['price'])

    # Sử dụng render_to_string để cập nhật phần tử HTML của giỏ hàng trên trang web mà không cần tải lại trang.
    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 
                                                          'cart_total_amount':cart_total_amount})
    
    # Trả về một đối tượng JsonResponse với HTML đã được render và tổng số sản phẩm trong giỏ hàng.
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})


def update_cart(request):

    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 
                                                             'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})



@login_required
def checkout_view(request):

    # Khởi tạo tổng giá trị giỏ hàng và tổng số tiền là 0
    cart_total_amount = 0
    total_amount = 0

    # Kiểm tra nếu có dữ liệu giỏ hàng trong session
    if 'cart_data_obj' in request.session:
        # Tính tổng giá trị đơn hàng từ giỏ hàng
        for p_id, item in request.session['cart_data_obj'].items():
            total_amount += int(item['qty']) * float(item['price'])

        # Tạo đơn hàng mới trong database
        order = CartOrder.objects.create(
            user = request.user,
            price = total_amount
        )

        # Tạo từng sản phẩm trong đơn hàng và lưu vào database
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

            cart_order_products = CartOrderItems.objects.create(
                order=order,
                invoice_no="INVOICE NO-" + str(order.id), 
                item=item['title'],
                image=item['image'],
                qty=item['qty'],
                price=item['price'],
                total=float(item['qty']) * float(item['price'])
            )

        # Cấu hình thông tin thanh toán PayPal
        host = request.get_host()
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': cart_total_amount,
            'item_name': "Order-Item-No-" + str(order.id),
            'invoice': "INVOICE_NO-" + str(order.id),
            'currency_code': "USD",
            'notify_url': 'http://{}{}'.format(host, reverse("core:paypal-ipn")),
            'return_url': 'http://{}{}'.format(host, reverse("core:payment-completed")),
            'cancel_url': 'http://{}{}'.format(host, reverse("core:payment-failed")),
        }

        # Tạo nút thanh toán PayPal
        paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)

        # Xử lý địa chỉ giao hàng
        try:
            active_address = Address.objects.get(user = request.user, status=True)
        except:
            # Hiển thị cảnh báo nếu có nhiều hơn một địa chỉ hoạt động
            messages.warning(request, "There are multiple addresses, only one should be activated.")
            active_address = None

         # Hiển thị trang thanh toán với các thông tin cần thiết
        return render(request, "core/checkout.html", {"cart_data":request.session['cart_data_obj'], 
                                                      'totalcartitems': len(request.session['cart_data_obj']), 
                                                      'cart_total_amount':cart_total_amount, 
                                                      'paypal_payment_button':paypal_payment_button, 
                                                      "active_address":active_address})



@login_required
def payment_completed_view(request):
    cart_total_amount = 0

    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    return render(request, 'core/payment-completed.html', 
                  {'cart_data':request.session['cart_data_obj'],
                   'totalcartitems':len(request.session['cart_data_obj']),
                   'cart_total_amount':cart_total_amount})

@login_required
def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')

@login_required
def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)

    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user = request.user,
            address = address,
            mobile = mobile,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")
    else:
        print("Error")
    
    user_profile = Profile.objects.get(user=request.user)
    print("User Profile is: #########################",  user_profile)

    context = {
        "user_profile": user_profile,
        "orders_list": orders_list,
        "address": address,
    }
    return render(request, 'core/dashboard.html', context)

def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderItems.objects.filter(order=order)

    context = {
        "order_items": order_items,
    }
    return render(request, 'core/order-detail.html', context)

def make_address_default(request):
    id = request.GET['id']
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({"boolean": True})

@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.all()
    context = {
        "w": wishlist
    }
    return render(request, "core/wishlist.html", context)

def add_to_wishlist(request):
    product_id = request.GET['id']
    product = Product.objects.get(id=product_id)
    print("Product ID is:" + product_id)

    context = {}

    wishlist_count = Wishlist.objects.filter(product=product, user=request.user).count()
    print(wishlist_count)

    if wishlist_count > 0:
        context = {
            "bool": True
        }
    else:
        new_wishlist = Wishlist.objects.create(
            user = request.user,
            product = product,
        )
        context = {
            "bool": True
        }

    return JsonResponse(context)

def remove_wishlist(request):
    pid = request.GET['id']
    wishlist = Wishlist.objects.filter(user=request.user)
    wishlist_d = Wishlist.objects.get(id=pid)
    delete_product = wishlist_d.delete()
    
    context = {
        "bool":True,
        "w":wishlist
    }
    wishlist_json = serializers.serialize('json', wishlist)
    t = render_to_string('core/async/wishlist-list.html', context)
    return JsonResponse({'data':t,'w':wishlist_json})

# Other Pages 
def contact(request):
    return render(request, "core/contact.html")


def ajax_contact_form(request):
    full_name = request.GET['full_name']
    email = request.GET['email']
    phone = request.GET['phone']
    subject = request.GET['subject']
    message = request.GET['message']

    contact = ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )

    data = {
        "bool": True,
        "message": "Message Sent Successfully"
    }

    return JsonResponse({"data":data})


def about_us(request):
    return render(request, "core/about_us.html")


def purchase_guide(request):
    return render(request, "core/purchase_guide.html")

def privacy_policy(request):
    return render(request, "core/privacy_policy.html")

def terms_of_service(request):
    return render(request, "core/terms_of_service.html")



