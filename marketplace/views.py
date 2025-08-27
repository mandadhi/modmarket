# marketplace/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.timezone import now
import gridfs
from bson import ObjectId
import re
from urllib.parse import quote
from django.contrib.admin.views.decorators import staff_member_required
import io , zipfile
from .forms import (
    ProductForm, DeveloperProfileForm, ReviewForm,
    ProductFileFormSet, ModerationForm,StyledUserCreationForm
)
from .models import (
    categories_all, category_get,
    developer_get_or_create, developer_update,
    product_create, product_get, products_find, products_count,
    product_inc_download, product_update, products_related,
    product_file_add, product_file_first, product_files_for,
    review_add, review_get_by_user, reviews_for_product,
    download_get_or_create, moderation_log_add,
    user_get,user_create,license_create,product_inc_review,refresh_product_rating,category_create
)
from .db import db

# ------------------------
# Constants
# ------------------------
TYPE_LABELS = {
    "project": "Project Source Code",
    "apk": "Modified APK",
    "template": "Template",
    "plugin": "Plugin/Extension",
}

FILE_TYPE_LABELS = {
    "main": "Main File",
    "demo": "Demo File",
    "documentation": "Documentation",
    "screenshot": "Screenshot",
    "license": "License File",
}

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_CONTENT_TYPES = [
    "application/zip",
    "application/octet-stream",
    "image/png",
    "image/jpeg",
    "application/pdf",
    "text/plain",
]

# ------------------------
# Helper Functions
# ------------------------
def _regex_contains(value):
    return {"$regex": re.escape(value), "$options": "i"}


def _validate_file(file):
    if file.size > MAX_UPLOAD_SIZE:
        raise ValueError("File too large.")
    if getattr(file, "content_type", None) not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported file type: {getattr(file, 'content_type', 'unknown')}")


def _save_file_to_gridfs(uploaded_file, bucket_name="products"):
    """Save a file to MongoDB GridFS and return metadata"""
    _validate_file(uploaded_file)
    fs = gridfs.GridFS(db, collection=bucket_name)
    file_id = fs.put(
        uploaded_file.read(),
        filename=uploaded_file.name,
        content_type=getattr(uploaded_file, "content_type", "application/octet-stream"),
        length=getattr(uploaded_file, "size", None)
    )
    return {
        "file_id": str(file_id),
        "filename": uploaded_file.name,
        "content_type": getattr(uploaded_file, "content_type", "application/octet-stream"),
        "size": getattr(uploaded_file, "size", 0),
        "bucket": bucket_name
    }


def serve_file(file_id, bucket_name="products", inline=False):
    """Serve a GridFS file via Django response"""
    fs = gridfs.GridFS(db, collection=bucket_name)
    try:
        grid_out = fs.get(ObjectId(file_id))
    except gridfs.NoFile:
        raise Http404("File not found.")
    response = HttpResponse(grid_out.read(), content_type=grid_out.content_type or "application/octet-stream")
    dispo_type = "inline" if inline else "attachment"
    response["Content-Disposition"] = f'{dispo_type}; filename="{quote(grid_out.filename)}"'
    return response


def serve_thumbnail(request, file_id):
    return serve_file(file_id, bucket_name="thumbnails", inline=True)
def serve_avatar(request, file_id):
    return serve_file(file_id, bucket_name="avatars", inline=True)

def download_product_file(request,file_id,bucket):
    return serve_file(file_id,bucket_name=bucket,inline=True)


# ------------------------
# Public Pages
# ------------------------
def home(request):
    featured = list(
        db.products.find({"status": "approved"})
        .sort("download_count", -1)
        .limit(8)
    )
    recent = list(
        db.products.find({"status": "approved"})
        .sort("created_at", -1)
        .limit(6)
    )
    categories_cursor = db.products.aggregate([
        {"$match": {"status": "approved"}},
        {"$unwind": "$category"},
        {"$group": {"_id": "$category"}},
        {"$limit": 6}
    ])

    categories = []
    for c in categories_cursor:
        val = c["_id"]
        if isinstance(val, dict) and "name" in val:
            categories.append({"category": val["name"]})
        elif isinstance(val, str):
            categories.append({"category": val})
    all_products = featured + recent
    for p in all_products:
        p_id = p.get("_id")
        if p_id:
            p["id"] = str(p_id)

        dev_id = p.get("developer_id")
        dev = db.developers.find_one({"_id": dev_id}) if dev_id else None
        if dev:
            dev["_id"] = str(dev["_id"])
            p["developer"] = dev
            user_id = dev.get("user_id")
            usr = db.users.find_one({"user_id": user_id}) if user_id else None
            if usr:
                usr["_id"] = str(usr["_id"])
                p["user"] = usr

    return render(request, "marketplace/home.html", {
        "featured_products": featured,
        "recent_products": recent,
        "categories": categories,
    })



from bson import ObjectId

def product_list(request):
    q = {"status": "approved"}
    query = request.GET.get("q")
    if query:
        q["$or"] = [
            {"title": _regex_contains(query)},
            {"description": _regex_contains(query)},
            {"tags": _regex_contains(query)}
        ]

    category_filter = request.GET.get("category")
    if category_filter:
        q["category"] = category_filter
    

    product_type = request.GET.get("type")
    if product_type:
        q["product_type"] = product_type

    price_filter = request.GET.get("price")
    if price_filter == "free":
        q["is_free"] = True
    elif price_filter == "paid":
        q["is_free"] = False

    sort_by = request.GET.get("sort", "-created_at")
    sort_map = {
        "-created_at": ("created_at", -1),
        "-download_count": ("download_count", -1),
        "-rating": ("rating", -1),
        "price": ("price", 1),
        "-price": ("price", -1)
    }
    sort_field, sort_dir = sort_map.get(sort_by, ("created_at", -1))

    page = int(request.GET.get("page", 1))
    per_page = 12
    total = products_count(q)
    skip = (page - 1) * per_page
    items = products_find(q, [(sort_field, sort_dir)], skip, per_page)
    for p in items:
        p["id"] = str(p["_id"])
        dev = db.developers.find_one({"_id": p.get("developer_id")})
        if dev:
            dev["id"] = str(dev["_id"])
            usr = db.users.find_one({"user_id": dev.get("user_id")})
            if usr:
                usr["id"] = str(usr["_id"])
                dev["user"] = usr
            p["developer"] = dev
        if p.get("category"):
            cat_objs = list(db.categories.find({"category": {"$in": p["category"]}}))
            categories_list = []
            for c in cat_objs:
                c["id"] = str(c["_id"])
                categories_list.append(c)
            p["categories"] = categories_list
        else:
            p["categories"] = []

    paginator = Paginator(range(total), per_page)
    page_obj = paginator.get_page(page)
    categories_cursor = db.products.aggregate([
        {"$match": {"status": "approved"}},
        {"$unwind": "$category"},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 0}}},
        {"$sort":{"_id":1}},
    ])
    categories = [{"category": c["_id"]} for c in categories_cursor]
    get_params = request.GET.copy()
    if "sort" in get_params:
        del get_params["sort"]
    querystring = get_params.urlencode()

    return render(request, "marketplace/product_list.html", {
        "items": items,
        "categories": categories,
        "current_category": category_filter,
        "current_type": product_type,
        "current_price": price_filter,
        "current_sort": sort_by,
        "query": query,
        "page_obj": page_obj,
        "querystring": querystring
    })

def product_detail(request, pk):
    product = None
    profile, is_admin = None, False

    if request.user.is_authenticated:
        profile, _ = developer_get_or_create(request.user.id)
        is_admin = request.user.is_staff
    if is_admin:
        product = db.products.find_one({"_id": pk})
    else:
        product = product_get(pk, status="approved")
        if not product and profile:
            product = db.products.find_one({"_id": pk, "developer_id": profile["_id"]})

    if not product:
        messages.error(request, "Product not found.")
        return redirect("home")

    product['id'] = product['_id']
    license = db.licenses.find_one({'product_id': product['_id']})
    files = list(db.product_files.find({"product_id": product["_id"]}))
    product["files"] = []
    product["screenshots"] = []

    for f in files:
        f["id"] = f["_id"]
        f["file_type_label"] = FILE_TYPE_LABELS.get(f.get("file_type"), f.get("file_type"))
        product["files"].append(f)
        if f.get("content_type", "").startswith("image/"):
            product["screenshots"].append({
                "id": f["_id"],         
                "filename": f["filename"],
                "path": f["path"],
                "content_type": f.get("content_type"),
                "file_type_label": f.get("file_type_label"),
                "size": f.get("size")
            })

    product["license_file"] = license
    product["user_details"] = db.users.find_one({"_id": product["user_id"]})
    product["product_type_label"] = TYPE_LABELS.get(product.get("product_type"), product.get("product_type"))
    dev = db.developers.find_one({"_id": product["developer_id"]})
    product['developer_doc'] = dev
    reviews=[]
    user_review=[]
    if product.get("status") == "approved":
        reviews = reviews_for_product(pk)
        if request.user.is_authenticated:
            user_review = review_get_by_user(request.user.id, pk)
    related = products_related(product.get("category"), pk, limit=4)
    refresh_product_rating(product['id'])

    return render(request, "marketplace/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "user_review": user_review,
        "can_review": request.user.is_authenticated and not user_review and product.get('status')=='approved',
        "related_products": related,
        "files": product_files_for(pk),
        "category": category_get(product.get("category_id"))
    })

@login_required
def download_product(request, pk):
    if not request.user.is_authenticated:
        messages.error(request, "Login required to download this product.")
        return redirect("login")

    profile, _ = developer_get_or_create(request.user.id)
    product = db.products.find_one({
        "$or": [
            {"_id": pk, "status": "approved"},
            {"_id": pk, "developer_id": profile["_id"]}
        ]
    })

    if not product:
        messages.error(request, "Product not available for download.")
        return redirect("home")
    main_file = db.product_files.find_one({"product_id": pk, "file_type": "main"})
    if not main_file:
        messages.error(request, "Main product file not found.")
        return redirect("product_detail", pk=pk)
    return serve_file(file_id=main_file["path"], bucket_name="products", inline=False)

# ------------------------
# Authentication
# ------------------------
def register(request):
    if request.method == "POST":
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            developer_get_or_create(user.id)
            user_create(user.id,user.username,user.email)
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("home")
    else:
        form = StyledUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


# ------------------------
# Developer
# ------------------------
@login_required
def developer_dashboard(request):
    profile, _ = developer_get_or_create(request.user.id)
    total_products_count = db.products.count_documents({"developer_id": profile["_id"]})
    my_products = list(db.products.find({"developer_id": profile["_id"]}).sort("created_at", -1))
    for p in my_products:
        p['id'] = p['_id']
    total_downloads = sum(p.get("download_count", 0) for p in my_products)
    pending_products = db.products.count_documents({
        "developer_id": profile["_id"],
        "status": "pending"
    })

    return render(request, "marketplace/developer_dashboard.html", {
        "profile": profile,
        "products": my_products,
        "total_products_count": total_products_count,
        "total_downloads": total_downloads,
        "pending_products": pending_products
    })



@login_required
def edit_profile(request):
    profile, _ = developer_get_or_create(request.user.id)
    if request.method == "POST":
        form = DeveloperProfileForm(request.POST, request.FILES)
        if form.is_valid():
            updates = {
                "company_name": form.cleaned_data.get("company_name", ""),
                "bio": form.cleaned_data.get("bio", ""),
                "website": form.cleaned_data.get("website", "")
            }
            if form.cleaned_data.get("avatar"):
                saved = _save_file_to_gridfs(form.cleaned_data["avatar"], "avatars")
                updates["avatar_path"] = saved["file_id"]
                updates["avatar_bucket"] = saved["bucket"]
            developer_update(request.user.id, updates)
            messages.success(request, "Profile updated successfully!")
            return redirect("developer_dashboard")
    else:
        form = DeveloperProfileForm(initial={
            "company_name": profile.get("company_name", ""),
            "bio": profile.get("bio", ""),
            "website": profile.get("website", "")
        })
    return render(request, "marketplace/edit_profile.html", {"form": form})


@login_required
def upload_product(request):
    profile, _ = developer_get_or_create(request.user.id)
    user = user_get(request.user.id)

    if not profile or not user:
        messages.error(request, "User or developer profile not found.")
        return redirect("developer_dashboard")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        file_formset = ProductFileFormSet(request.POST, request.FILES, prefix="files")

        if form.is_valid() and file_formset.is_valid():
            data = form.cleaned_data
            categories = data.get("category", [])
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(",") if c.strip()]
            else:
                categories = [str(c).strip() for c in categories if c and str(c).strip()]
            product_payload = {
                "title": data["title"],
                "description": data["description"],
                "developer_id": profile["_id"],
                "category": categories,
                "license": data.get("license"),
                "product_type": data["product_type"],
                "version": data["version"],
                "price": float(data.get("price") or 0),
                "is_free": bool(data.get("is_free") or False),
                "status": "pending",
                "user_id": user["_id"],
                "tags": [t.strip() for t in data.get("tags", "").split(",") if t.strip()]
            }
            if data.get("thumbnail"):
                saved = _save_file_to_gridfs(data["thumbnail"], "thumbnails")
                product_payload["thumbnail_path"] = saved["file_id"]
                product_payload["thumbnail_bucket"] = saved["bucket"]
            product_id = product_create(product_payload)
            if categories:
                category_create(product_id, categories)
            if data.get("license_file"):
                saved_license = _save_file_to_gridfs(data["license_file"], "license")
                license_create(
                    product_id=product_id,
                    path=saved_license["file_id"],
                    filename=saved_license["filename"],
                    size=saved_license["size"],
                    bucket=saved_license["bucket"]
                )
            for fform in file_formset:
                if fform.cleaned_data and not fform.cleaned_data.get("DELETE"):
                    uploaded_file = fform.cleaned_data.get("file")
                    file_type = fform.cleaned_data.get("file_type")
                    if uploaded_file:
                        saved_file = _save_file_to_gridfs(uploaded_file, "products")
                        product_file_add(
                            product_id=product_id,
                            file_type=file_type,
                            path=saved_file["file_id"],
                            filename=saved_file["filename"],
                            size=saved_file["size"],
                            bucket=saved_file["bucket"],
                            content_type=uploaded_file.content_type
                        )

            messages.success(request, "Product uploaded! Awaiting review.")
            return redirect("developer_dashboard")

    else:
        form = ProductForm()
        file_formset = ProductFileFormSet(prefix="files")

    return render(request, "marketplace/upload_product.html", {
        "form": form,
        "file_formset": file_formset
    })

# ------------------------
# Reviews
# ------------------------
@login_required
@require_POST
def add_review(request, pk):
    product = product_get(pk, status="approved")
    if not product:
        raise Http404("Product not found.")
    if review_get_by_user(request.user.id, pk):
        messages.error(request, "You have already reviewed this product.")
        return redirect("product_detail", pk=pk)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review_add(
            request.user.id,
            pk,
            int(form.cleaned_data["rating"]),
            form.cleaned_data.get("comment", "")
        )
        reviews = list(db.reviews.find({"product_id": ObjectId(pk)}))
        if reviews:
            total = sum(r["rating"] for r in reviews)
            count = len(reviews)
            avg = round(total / count, 1)
        else:
            avg = 0
            count = 0
        db.products.update_one(
            {"_id": pk},
            {"$set": {
                "rating": avg,
                "review_count": count,
                "updated_at": now()
            }}
        )

        messages.success(request, "Review added successfully!")

    return redirect("product_detail", pk=pk)




# ------------------------
# Moderation
# ------------------------
@user_passes_test(lambda u: u.is_staff)
def moderation_queue(request):
    pending_products = list(db.products.find({"status": "pending"}).sort("created_at", -1))
    for p in pending_products:
        p["id"] = str(p["_id"])
        p["product_type_label"] = TYPE_LABELS.get(p.get("product_type"), p.get("product_type"))
        files = list(db.product_files.find({"product_id": p["_id"]}))
        for f in files:
            f["id"] = str(f["_id"])
            f["file_type_label"] = FILE_TYPE_LABELS.get(f.get("file_type"), f.get("file_type"))
        p["files"] = files
        p["developer"] = db.developers.find_one({"_id": p["developer_id"]})
    return render(request, "marketplace/moderation_queue.html", {"pending_products": pending_products})


@user_passes_test(lambda u: u.is_staff)
def moderate_product(request, pk):
    product = product_get(pk)
    if not product:
        messages.error(request, "Product not found.")
        return redirect("moderation_queue")

    developer_id = product["developer_id"]
    product["developer"] = db.developers.find_one({"_id": developer_id})
    license = db.licenses.find_one({'product_id': product['_id']})
    files = list(db.product_files.find({"product_id": product["_id"]}))
    for f in files:
        f["id"] = f["_id"]
        f["file_type_label"] = FILE_TYPE_LABELS.get(f.get("file_type"), f.get("file_type"))
    product["files"] = files
    product["license_file"] = license
    product["user_details"] = db.users.find_one({"_id": product["user_id"]})
    product["product_type_label"] = TYPE_LABELS.get(product.get("product_type"), product.get("product_type"))
    total_products = db.products.count_documents({"developer_id": developer_id})
    approved_products = db.products.count_documents({"developer_id": developer_id, "status": "approved"})
    pending_products = db.products.count_documents({"developer_id": developer_id, "status": "pending"})
    rejected_products = db.products.count_documents({"developer_id": developer_id, "status": "rejected"})

    if request.method == "POST":
        form = ModerationForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            reason = form.cleaned_data.get("reason", "")
            product_update(pk, {"status": action})
            moderation_log_add(pk, request.user.id, action, reason)
            messages.success(request, f"Product {action} successfully!")
            return redirect("moderation_queue")
    else:
        form = ModerationForm()

    return render(request, "marketplace/moderate_product.html", {
        "product": product,
        "form": form,
        "total_products": total_products,
        "approved_products": approved_products,
        "pending_products": pending_products,
        "rejected_products": rejected_products,
    })


# ------------------------
# Category Management
# ------------------------
@staff_member_required
def admin_category_list(request):
    categories = list(db.categories.find().sort("category", 1))
    for c in categories:
        c["id"] = c["_id"]
    return render(request, "admin/categories_list.html", {"categories": categories})

@staff_member_required
def manage(request):
    return render(request,'admin/admin_dashboard.html')

@staff_member_required
def admin_category_add(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            category_names = [c.strip() for c in name.split(",") if c.strip()]
            if not category_names:
                messages.error(request, "Please provide at least one category.")
                return redirect("admin_category_add")
            for cname in category_names:
                exists = db.categories.find_one({"category": cname})
                if exists:
                    continue
                db.categories.insert_one({
                    "_id": str(ObjectId()),
                    "category": cname,
                    "created_at": now()
                })

            messages.success(request, f"Added {len(category_names)} categories successfully.")
            return redirect("admin_category_list")

        messages.error(request, "Name is required.")
    return render(request, "admin/category_form.html")

@staff_member_required
def admin_category_edit(request, pk):
    try:
        pk = pk
    except:
        messages.error(request, "Invalid category ID.")
        return redirect("admin_category_list")

    cat = db.categories.find_one({"_id": pk})
    if not cat:
        messages.error(request, "Category not found.")
        return redirect("admin_category_list")

    if request.method == "POST":
        new_name = request.POST.get("name")
        if new_name:
            old_name = cat["category"]
            db.categories.update_one(
                {"_id": pk},
                {"$set": {"category": new_name}}
            )
            db.products.update_many(
                {"category": old_name},
                {
                    "$set": {"category.$": new_name}
                }
            )
            messages.success(request, "Category updated and applied to products.")
            return redirect("admin_category_list")
        messages.error(request, "Name is required.")

    return render(request, "admin/category_form.html", {"category": cat})


@staff_member_required
def admin_category_delete(request, pk):
    db.categories.delete_one({"_id": pk})
    messages.success(request, "Category deleted.")
    return redirect("admin_category_list")


# ------------------------
# Product Management
# ------------------------
@staff_member_required
def admin_product_list(request):
    products = list(db.products.find().sort("created_at", -1))
    for p in products:
        p["id"] = str(p["_id"])
    return render(request, "admin/products_list.html", {"products": products})


@staff_member_required
def admin_product_delete(request, pk):
    db.products.delete_one({"_id":pk})
    messages.success(request, "Product deleted.")
    return redirect("admin_product_list")


# ------------------------
# Developer Management
# ------------------------
@staff_member_required
def admin_developer_list(request):
    devs = list(db.developers.find().sort("created_at", -1))
    for d in devs:
        d["id"] = str(d["_id"])
        d['user']=db.users.find_one({'user_id':d['user_id']})
    return render(request, "admin/developers_list.html", {"developers": devs})


@staff_member_required
def admin_developer_delete(request, pk):
    db.developers.delete_one({"_id": pk})
    messages.success(request, "Developer deleted.")
    return redirect("admin_developer_list")

@staff_member_required
def admin_developer_view(request,pk):
    devs = db.developers.find_one({'_id':pk})
    if not devs:
        messages.error(request, "Developer not found.")
        return redirect("admin_developer_list")
    devs["id"] = devs["_id"]
    devs['user']=db.users.find_one({'user_id':devs['user_id']})
    products=list(db.products.find({'developer_id':devs["id"]}))
    for p in products:
        p['id']=p['_id']
    approved_products = list(db.products.find({'developer_id':devs["id"],'status':"approved"}))
    for a in approved_products:
        a['id']=a['_id']
    pending_products = list(db.products.find({'developer_id':devs["id"],'status':"pending"}))
    for p in pending_products:
        p['id']=p['_id']
    rejected_products = list(db.products.find({'developer_id':devs["id"],'status':"rejected"}))
    for r in rejected_products:
        r['id']=r['_id']
    context = {
    "developers": devs,
    "products": products,
    "approved_products": approved_products,
    "pending_products": pending_products,
    "rejected_products": rejected_products,
    }
    return render(request, 'marketplace/developer_profile.html', context)

def developer_profile(request,pk):
    devs = db.developers.find_one({'_id':pk})
    if not devs:
        messages.error(request, "Developer not found.")
        return redirect("admin_developer_list")
    devs["id"] = devs["_id"]
    devs['user']=db.users.find_one({'user_id':devs['user_id']})
    products=list(db.products.find({'developer_id':devs["id"]}))
    for p in products:
        p['id']=p['_id']
    approved_products = list(db.products.find({'developer_id':devs["id"],'status':"approved"}))
    for a in approved_products:
        a['id']=a['_id']
    pending_products = list(db.products.find({'developer_id':devs["id"],'status':"pending"}))
    for p in pending_products:
        p['id']=p['_id']
    rejected_products = list(db.products.find({'developer_id':devs["id"],'status':"rejected"}))
    for r in rejected_products:
        r['id']=r['_id']
    context = {
    "developers": devs,
    "products": products,
    "approved_products": approved_products,
    "pending_products": pending_products,
    "rejected_products": rejected_products,
    }
    return render(request, 'marketplace/developer_profile.html', context)
