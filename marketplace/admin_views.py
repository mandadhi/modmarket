# marketplace/admin_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import (
    categories_all, category_get,
    products_find, products_count, product_update,
    developer_get_or_create, reviews_for_product,
    moderation_log_add
)

# Only staff can access
def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff)
def admin_dashboard(request):
    stats = {
        "categories": categories_all(),
        "total_products": products_count({}),
        "pending_products": products_count({"status": "pending"}),
        "approved_products": products_count({"status": "approved"}),
    }
    return render(request, "admin/dashboard.html", {"stats": stats})

@user_passes_test(is_staff)
def admin_products(request):
    q = {}
    status = request.GET.get("status")
    if status:
        q["status"] = status

    items = products_find(q, [("created_at", -1)], skip=0, limit=50)
    return render(request, "admin/products.html", {"products": items})

@user_passes_test(is_staff)
def admin_moderate(request, pk):
    product = category_get(pk)  # use your product_get here if needed
    if request.method == "POST":
        action = request.POST.get("action")
        reason = request.POST.get("reason", "")
        product_update(pk, {"status": action})
        moderation_log_add(pk, request.user.id, action, reason)
        messages.success(request, f"Product {action} successfully!")
        return redirect("admin_products")
    return render(request, "admin/moderate.html", {"product": product})