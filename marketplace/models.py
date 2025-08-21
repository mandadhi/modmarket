from datetime import datetime
from bson import ObjectId
from .db import db

# --------- Users ----------
def user_get(user_id: int):
    return db.users.find_one({"user_id": user_id})

def user_create(django_id: int, username: str, email: str):
    if not db.users.find_one({"user_id": django_id}):
        payload = {
            "_id": str(ObjectId()),  # MongoDB ObjectId as string
            "user_id": django_id,  # reference to Django user
            "username": username,
            "email": email,
            "created_at": datetime.now(),
        }
        db.users.insert_one(payload)
def user_update(user_id: int, updates: dict):
    return db.users.update_one({"_id": int(user_id)}, {"$set": updates})


# --------- Categories ----------
def categories_all(limit=None):
    cats = db.categories.distinct("category")
    if limit:
        cats = cats[:int(limit)]
    return [{"category": c} for c in cats]

def category_get(cat_id: str):
    return db.categories.find_one({"_id": str(cat_id)})

def category_create(product_id: str, data: list):
    for c in data:
        # skip empty or None categories
        if not c or not str(c).strip():
            continue

        c = str(c).strip()  # ensure string
        existing = db.categories.find_one({'category': c})
        if not existing:
            db.categories.insert_one({
                '_id': str(ObjectId()),
                'product_id': product_id,
                'category': c,
            })

# --------- Developers ----------
def developer_get_or_create(user_id: int):
    doc = db.developers.find_one({"user_id": int(user_id)})
    if doc:
        return doc, False
    payload = {
        "_id": str(ObjectId()),
        "user_id": int(user_id),
        "company_name": "",
        "bio": "",
        "website": "",
        "avatar_path": None,
        "is_verified": False,
        "rating": 0.0,
        "total_sales": 0,
        "created_at": datetime.now(),
    }
    db.developers.insert_one(payload)
    return payload, True

def developer_update(user_id: int, updates: dict):
    return db.developers.update_one({"user_id": int(user_id)}, {"$set": updates})


# --------- Licenses ----------
def license_create(product_id: str, path: str, filename: str, size: int, checksum: str | None = None,bucket: str | None = None):
    payload = {
        "_id": str(ObjectId()),
        "product_id": product_id,
        "file_type": "License",
        "path": path,
        "filename": filename,
        "file_size": int(size),
        "scan_status": "pending",
        "scan_results": {},
        "uploaded_at": datetime.now(),
        "bucket": bucket or "license",
    }
    db.licenses.insert_one(payload)
    return payload["_id"]

def license_get(license_id: str):
    return db.licenses.find_one({"_id": license_id})

def licenses_all():
    return list(db.licenses.find({}))


# --------- Products ----------
def product_create(data: dict):
    _id = str(ObjectId())
    data["_id"] = _id
    data.setdefault("status", "pending")
    data.setdefault("download_count", 0)
    data.setdefault("rating", 0.0)
    data.setdefault("review_count", 0)
    data["created_at"] = datetime.now()
    data["updated_at"] = datetime.now()
    db.products.insert_one(data)
    return _id

def product_get(pk: str, status=None):
    q = {"_id": pk}
    if status:
        q["status"] = status
    product = db.products.find_one(q)
    if product:
        # attach developer + user info
        dev = db.developers.find_one({"_id": product.get("developer_id")})
        if dev:
            user = user_get(dev["user_id"])
            product["developer"] = {**dev, "user": user}
    return product

def products_find(q: dict, sort: list, skip: int, limit: int):
    cur = db.products.find(q).sort(sort).skip(skip).limit(limit)
    return list(cur)

def products_count(q: dict):
    return db.products.count_documents(q)

def product_inc_download(pk: str):
    db.products.update_one({"_id": pk}, {"$inc": {"download_count": 1}})
def product_inc_review(pk: str):
    db.products.update_one({"_id": pk}, {"$inc": {"review_count": 1}})

def product_update(pk: str, updates: dict):
    updates["updated_at"] = datetime.now()
    db.products.update_one({"_id": pk}, {"$set": updates})

def products_related(category_id: str, exclude_id: str, limit: int = 4):
    cur = db.products.find({
        "category_id": category_id,
        "status": "approved",
        "_id": {"$ne": exclude_id}
    }).limit(limit)
    return list(cur)


# --------- Product Files ----------
def product_file_add(product_id: str, file_type: str, path: str, filename: str, size: int, checksum: str | None = None,bucket: str | None = None,content_type=None):
    payload = {
        "_id": str(ObjectId()),
        "product_id": product_id,
        "file_type": file_type,
        "path": path,
        "filename": filename,
        "file_size": int(size),
        "checksum": checksum or "",
        "scan_status": "pending",
        "scan_results": {},
        "uploaded_at": datetime.now(),
        "bucket": bucket or "products",
        "content_type": content_type,
    }
    db.product_files.insert_one(payload)
    return payload["_id"]

def product_file_first(product_id: str, file_type: str):
    return db.product_files.find_one({"product_id": product_id, "file_type": file_type})

def product_files_for(product_id: str):
    return list(db.product_files.find({"product_id": product_id}).sort("uploaded_at", -1))


# --------- Reviews ----------
from bson import ObjectId
from datetime import datetime

def review_add(user_id, product_id, rating, comment=""):
    if isinstance(product_id, str):
        product_id = ObjectId(product_id)
    db.reviews.insert_one({
        "user_id": user_id,
        "product_id": product_id,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now()
    })


def review_get_by_user(user_id, product_id):
    if isinstance(product_id, str):
        product_id = ObjectId(product_id)
    return db.reviews.find_one({"user_id": user_id, "product_id": product_id})


def reviews_for_product(product_id: str):
    if isinstance(product_id, str):
        product_id = ObjectId(product_id)
    reviews = list(db.reviews.find({"product_id": product_id}).sort("created_at", -1))
    for r in reviews:
        r["user"] = user_get(r["user_id"])   # attach user info
    return reviews


def refresh_product_rating(product_id: str):
    pipeline = [
        {"$match": {"product_id": product_id}},  # product_id is a string
        {"$group": {
            "_id": "$product_id",
            "avg": {"$avg": "$rating"},
            "count": {"$sum": 1}
        }},
    ]
    agg = list(db.reviews.aggregate(pipeline))
    if agg:
        avg = round(float(agg[0]["avg"]), 2)
        count = int(agg[0]["count"])
    else:
        avg, count = 0.0, 0

    db.products.update_one(
        {"_id": product_id},  # also a string
        {"$set": {"rating": avg, "review_count": count}}
    )



# --------- Downloads ----------
def download_get_or_create(user_id: int, product_id: str, ip: str, ua: str):
    existing = db.downloads.find_one({"user_id": int(user_id), "product_id": product_id})
    if existing:
        return existing, False
    payload = {
        "_id": str(ObjectId()),
        "user_id": int(user_id),
        "product_id": product_id,
        "downloaded_at": datetime.now(),
        "ip_address": ip,
        "user_agent": ua,
    }
    db.downloads.insert_one(payload)
    return payload, True


# --------- Moderation ----------
def moderation_log_add(product_id: str, moderator_id: int, action: str, reason: str = ""):
    payload = {
        "_id": str(ObjectId()),
        "product_id": product_id,
        "moderator_id": int(moderator_id),
        "action": action,
        "reason": reason or "",
        "created_at": datetime.now(),
    }
    db.moderation_logs.insert_one(payload)
