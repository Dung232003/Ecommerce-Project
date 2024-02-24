from django.urls import path, include
from core.views import about_us, ajax_contact_form, checkout_view, filter_products, index, payment_completed_view, payment_failed_view, privacy_policy, product_list_view, product_detail_view, category_list_view, category_product_list_view, purchase_guide, terms_of_service, vendor_list_view, vendor_detail_view, tag_list, ajax_add_review, search_view
from core.views import add_to_cart, cart_view, delete_item_from_cart, update_cart
from core.views import payment_completed_view, payment_failed_view, customer_dashboard, order_detail, make_address_default
from core.views import wishlist_view, add_to_wishlist, remove_wishlist
from core.views import contact

app_name = "core"

urlpatterns = [
    # Homepage
    path("", index, name = "index"),
    path("products/", product_list_view, name = "products-list"),
    path("product/<pid>/", product_detail_view, name = "product-detail"),

    # Category
    path("category/", category_list_view, name = "category-list"),
    path("category/<cid>/", category_product_list_view, name = "category-product-list"),
    
    # Vendor
    path("vendors/", vendor_list_view , name = "vendor-list"),
    path("vendor/<vid>/", vendor_detail_view , name = "vendor-detail"),

    # Tags
    path("products/tag/<slug:tag_slug>/", tag_list, name = "tags"),

    # Add Review
    path("ajax-add-review/<pid>/", ajax_add_review, name="ajax-add-review"),

    # Search
    path("search/", search_view, name="search"),

    # Filter product
    path("filter-products/", filter_products, name="filter-product"),

    # Add to Cart
    path("add-to-cart/", add_to_cart, name="add-to-cart"),

    # Cart Page
    path("cart/", cart_view, name="cart"),

    # Delete Item from Cart
    path("delete-from-cart/", delete_item_from_cart, name="delete-from-cart"),

    # Update Cart
    path("update-cart/", update_cart, name="update-cart"),

    # Check-out 
    path("checkout/", checkout_view, name="checkout"),

    # Paypal
    path('paypal/', include('paypal.standard.ipn.urls')),

    # Payment Successful
    path("payment-completed/", payment_completed_view, name="payment-completed"),

    # Payment Failed
    path("payment-failed/", payment_failed_view, name="payment-failed"),

    # Dahboard
    path("dashboard/", customer_dashboard, name="dashboard"),

    # Order Detail
    path("dashboard/order/<int:id>", order_detail, name="order-detail"),

    # Making address default
    path("make-default-address/", make_address_default, name="make-default-address"),

    # Wishlist page
    path("wishlist/", wishlist_view, name="wishlist"),

    # adding to wishlist
    path("add-to-wishlist/", add_to_wishlist, name="add-to-wishlist"),

    # Removing from wishlist
    path("remove-from-wishlist/", remove_wishlist, name="remove-from-wishlist"),

    path("contact/", contact, name="contact"),
    path("ajax-contact-form/", ajax_contact_form, name="ajax-contact-form"),

    path("about_us/", about_us, name="about_us"),

    path("purchase_guide/", purchase_guide, name="purchase_guide"),

    path("privacy_policy/", privacy_policy, name="privacy_policy"),
    
    path("terms_of_service/", terms_of_service, name="terms_of_service"),
]