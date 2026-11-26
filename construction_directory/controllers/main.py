import base64
import json
import re
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image, UnidentifiedImageError

from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

WEEKDAYS = (
    ("mon", "จันทร์", "จ."),
    ("tue", "อังคาร", "อ."),
    ("wed", "พุธ", "พ."),
    ("thu", "พฤหัสบดี", "พฤ."),
    ("fri", "ศุกร์", "ศ."),
    ("sat", "เสาร์", "ส."),
    ("sun", "อาทิตย์", "อา."),
)


class ConstructionDirectoryPortalHome(CustomerPortal):
    @http.route()
    def home(self, **kw):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if vendor and not vendor.is_published:
            return request.redirect("/my/vendor/status")
        return super().home(**kw)


class ConstructionDirectoryController(http.Controller):
    @staticmethod
    def _social_url(value, allowed_domains):
        value = (value or "").strip()
        if not value:
            return ""
        if "://" not in value:
            value = "https://" + value
        parsed = urlparse(value)
        hostname = (parsed.hostname or "").lower()
        valid_domain = any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in allowed_domains
        )
        if parsed.scheme != "https" or not valid_domain:
            return False
        return value

    @staticmethod
    def _read_image_upload(upload):
        if not upload or not upload.filename:
            return False, False
        if not upload.mimetype or not upload.mimetype.startswith("image/"):
            return False, "Please upload an image file."
        image_bytes = upload.read(5 * 1024 * 1024 + 1)
        if len(image_bytes) > 5 * 1024 * 1024:
            return False, "Each image must be 5 MB or smaller."
        try:
            Image.open(BytesIO(image_bytes)).verify()
            return base64.b64encode(image_bytes), False
        except (UnidentifiedImageError, OSError):
            return False, "Please upload a valid image file."

    def _read_multiple_image_uploads(self, input_name, limit=7):
        uploads = [
            upload for upload in request.httprequest.files.getlist(input_name)
            if upload and upload.filename
        ]
        if len(uploads) > limit:
            return False, f"เลือกภาพได้ไม่เกิน {limit} รูป"
        image_data = []
        for upload in uploads:
            data, error = self._read_image_upload(upload)
            if error:
                return False, error
            if data:
                image_data.append(data)
        return image_data, False

    @staticmethod
    def _schedule_for_form(serialized):
        try:
            saved = json.loads(serialized or "{}")
        except (TypeError, ValueError):
            saved = {}
        return {
            code: {
                "open": code in saved,
                "from": (saved.get(code) or {}).get("from", ""),
                "to": (saved.get(code) or {}).get("to", ""),
            }
            for code, _label, _short in WEEKDAYS
        }

    @staticmethod
    def _schedule_from_post(post):
        form_schedule = {}
        saved = {}
        display_lines = []
        error = False
        for code, _label, short_label in WEEKDAYS:
            is_open = post.get(f"hours_{code}_open") in ("1", "on", "true")
            start = (post.get(f"hours_{code}_from") or "").strip()
            end = (post.get(f"hours_{code}_to") or "").strip()
            form_schedule[code] = {"open": is_open, "from": start, "to": end}
            if not is_open:
                continue
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start) or not re.fullmatch(
                r"(?:[01]\d|2[0-3]):[0-5]\d", end
            ):
                error = "กรุณาเลือกเวลาเปิดและเวลาปิดให้ครบในวันที่เลือกเปิดทำการ"
                continue
            if start >= end:
                error = "เวลาปิดต้องอยู่หลังเวลาเปิดในแต่ละวัน"
                continue
            saved[code] = {"from": start, "to": end}
            display_lines.append(f"{short_label} {start}–{end}")
        serialized = json.dumps(saved, ensure_ascii=False) if saved else ""
        return form_schedule, serialized, "\n".join(display_lines), error

    def _filters(self, province_id=None, category_id=None):
        provinces = request.env["res.country.state"].sudo().search(
            [("country_id.code", "=", "TH")], order="name"
        )
        categories = request.env["construction.vendor.category"].sudo().search(
            [("active", "=", True)], order="sequence, name"
        )
        try:
            selected_province_id = int(province_id or 0)
        except (TypeError, ValueError):
            selected_province_id = 0
        try:
            selected_category_id = int(category_id or 0)
        except (TypeError, ValueError):
            selected_category_id = 0
        return provinces, categories, selected_province_id, selected_category_id

    @http.route("/vendors", type="http", auth="public", website=True, sitemap=True)
    def vendors(self, q=None, province_id=None, category_id=None, **kwargs):
        provinces, categories, selected_province_id, selected_category_id = self._filters(
            province_id, category_id
        )
        domain = [("is_published", "=", True)]
        if q:
            term = q.strip()
            if term:
                domain += [
                    "|",
                    "|",
                    "|",
                    ("name", "ilike", term),
                    ("description", "ilike", term),
                    ("category_ids.name", "ilike", term),
                    ("public_product_ids.name", "ilike", term),
                ]
        if selected_province_id:
            domain.append(("province_id", "=", selected_province_id))
        if selected_category_id:
            domain += [
                "|",
                ("category_ids", "in", [selected_category_id]),
                ("public_product_ids.category_id", "=", selected_category_id),
            ]
        category_landing = not (
            (q or "").strip() or selected_province_id or selected_category_id
        )
        vendor_model = request.env["construction.vendor"].sudo()
        today = fields.Date.context_today(request.env.user)
        sponsored_domain = domain + [
            ("is_sponsored", "=", True),
            "|",
            ("sponsor_start", "=", False),
            ("sponsor_start", "<=", today),
            "|",
            ("sponsor_end", "=", False),
            ("sponsor_end", ">=", today),
        ]
        sponsored_vendors = vendor_model.search(
            sponsored_domain, order="sequence, name"
        )
        vendors = vendor_model.search(
            domain + [("id", "not in", sponsored_vendors.ids)],
            order="featured desc, sequence, name",
        )
        return request.render(
            "construction_directory.vendor_list",
            {
                "vendors": vendors,
                "sponsored_vendors": sponsored_vendors,
                "provinces": provinces,
                "categories": categories,
                "selected_province_id": selected_province_id,
                "selected_category_id": selected_category_id,
                "search_term": q or "",
                "category_landing": category_landing,
            },
        )

    @http.route(
        "/vendors/<int:vendor_id>",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def vendor_detail(self, vendor_id, **kwargs):
        vendor = request.env["construction.vendor"].sudo().search(
            [("id", "=", vendor_id), ("is_published", "=", True)], limit=1
        )
        if not vendor:
            return request.not_found()
        products = request.env["construction.vendor.product"].sudo().search(
            [("vendor_id", "=", vendor.id), ("active", "=", True), ("is_published", "=", True)],
            order="sequence, name",
        )
        return request.render(
            "construction_directory.vendor_detail", {"vendor": vendor, "products": products}
        )

    @http.route(
        "/directory/products/<int:product_id>",
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def product_detail(self, product_id, **kwargs):
        product = request.env["construction.vendor.product"].sudo().search(
            [
                ("id", "=", product_id),
                ("active", "=", True),
                ("is_published", "=", True),
                ("vendor_id.is_published", "=", True),
            ],
            limit=1,
        )
        if not product:
            return request.not_found()
        return request.render(
            "construction_directory.product_detail",
            {"product": product, "vendor": product.vendor_id},
        )

    @http.route("/privacy-notice", type="http", auth="public", website=True, sitemap=True)
    def privacy_notice(self, **kwargs):
        return request.render("construction_directory.privacy_notice", {})

    @http.route(
        "/vendors/register",
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        sitemap=False,
    )
    def vendor_register(self, **post):
        provinces, categories, _province_id, _category_id = self._filters()
        error = False
        schedule_form = self._schedule_for_form("")
        if request.httprequest.method == "POST":
            schedule_form, working_schedule, working_hours, schedule_error = self._schedule_from_post(post)
            name = (post.get("name") or "").strip()
            username = (post.get("username") or "").strip().lower()
            password = post.get("password") or ""
            password_confirm = post.get("password_confirm") or ""
            account_email = (post.get("account_email") or "").strip().lower()
            contact_email = (post.get("contact_email") or "").strip()
            province_id = post.get("province_id")
            image_data, image_error = self._read_image_upload(
                request.httprequest.files.get("image")
            )
            cover_data, cover_error = self._read_image_upload(
                request.httprequest.files.get("cover_image")
            )
            representative_data, representative_error = self._read_image_upload(
                request.httprequest.files.get("representative_image")
            )
            line_url = self._social_url(
                post.get("line_url"), ("line.me", "lin.ee")
            )
            facebook_url = self._social_url(
                post.get("facebook_url"), ("facebook.com", "fb.com", "m.me")
            )
            if line_url is False or facebook_url is False:
                error = "กรุณากรอกลิงก์ LINE หรือ Facebook ที่ถูกต้อง โดยใช้ลิงก์ HTTPS"
            error = image_error or cover_error or representative_error or error
            if not name or not province_id:
                error = "กรุณากรอกชื่อบริษัทและเลือกจังหวัด"
            else:
                try:
                    province_id = int(province_id)
                except (TypeError, ValueError):
                    province_id = 0
                province = provinces.filtered(lambda item: item.id == province_id)
                if not province:
                    error = "กรุณาเลือกจังหวัดในประเทศไทย"
            if not re.fullmatch(r"[a-z0-9._-]{4,32}", username):
                error = "Username must be 4–32 characters using a-z, 0-9, dot, dash, or underscore."
            elif request.env["res.users"].sudo().search_count([("login", "=", username)]):
                error = "This username is already in use. Please choose another."
            if not account_email or "@" not in account_email:
                error = "Please enter a valid email address for your account."
            if len(password) < 10:
                error = "Password must be at least 10 characters long."
            elif password != password_confirm:
                error = "Password and confirmation do not match."
            if not post.get("publication_consent"):
                error = "กรุณายินยอมให้เผยแพร่ข้อมูลบริษัทและช่องทางติดต่อก่อนส่งข้อมูล"
            if schedule_error:
                error = schedule_error
            if not error:
                category_ids = []
                for category_id in request.httprequest.form.getlist("category_ids"):
                    try:
                        category_ids.append(int(category_id))
                    except (TypeError, ValueError):
                        continue
                allowed_categories = categories.filtered(lambda item: item.id in category_ids)
                user = request.env["res.users"].sudo().with_context(
                    no_reset_password=True, mail_create_nosubscribe=True
                ).create(
                    {
                        "name": (post.get("contact_name") or "").strip() or name,
                        "login": username,
                        "email": account_email,
                        "password": password,
                        "group_ids": [(6, 0, [request.env.ref("base.group_portal").id])],
                    }
                )
                request.env["construction.vendor"].sudo().create(
                    {
                        "name": name,
                        "user_id": user.id,
                        "image_1920": image_data,
                        "cover_image": cover_data,
                        "representative_image": representative_data,
                        "province_id": province.id,
                        "district": (post.get("district") or "").strip(),
                        "contact_name": (post.get("contact_name") or "").strip(),
                        "working_hours": working_hours,
                        "working_schedule": working_schedule,
                        "contact_phone": (post.get("contact_phone") or "").strip(),
                        "contact_email": contact_email,
                        "website_url": (post.get("website_url") or "").strip(),
                        "line_url": line_url,
                        "facebook_url": facebook_url,
                        "publication_consent": True,
                        "publication_consent_date": fields.Datetime.now(),
                        "category_ids": [(6, 0, allowed_categories.ids)],
                        "is_published": False,
                    }
                )
                request.session.authenticate(
                    request.env,
                    {"login": username, "password": password, "type": "password"},
                )
                return request.redirect("/my/vendor/welcome")
        return request.render(
            "construction_directory.vendor_register",
            {"provinces": provinces, "categories": categories, "error": error, "form": post,
             "weekdays": WEEKDAYS, "schedule": schedule_form},
        )

    @http.route("/my/vendor", type="http", auth="user", website=True)
    def my_vendor(self, **kwargs):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if not vendor:
            return request.not_found()
        provinces, categories, _province_id, _category_id = self._filters()
        revision = request.env["construction.vendor.profile.revision"].search(
            [("vendor_id", "=", vendor.id)], limit=1
        )
        return request.render(
            "construction_directory.portal_vendor_profile",
            {"vendor": vendor, "provinces": provinces, "categories": categories, "error": False,
             "revision": revision, "weekdays": WEEKDAYS,
             "schedule": self._schedule_for_form((revision or vendor).working_schedule)},
        )

    @http.route("/my/vendor/status", type="http", auth="user", website=True)
    @http.route("/my/vendor/welcome", type="http", auth="user", website=True)
    def my_vendor_welcome(self, **kwargs):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if not vendor:
            return request.not_found()
        if vendor.is_published:
            return request.redirect("/my/vendor")
        return request.render(
            "construction_directory.portal_vendor_welcome", {"vendor": vendor}
        )

    @http.route(
        "/my/vendor/save", type="http", auth="user", website=True,
        methods=["POST"], csrf=True,
    )
    def my_vendor_save(self, **post):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if not vendor:
            return request.not_found()
        provinces, categories, _province_id, _category_id = self._filters()
        schedule_form, working_schedule, working_hours, schedule_error = self._schedule_from_post(post)
        try:
            province_id = int(post.get("province_id") or 0)
        except (TypeError, ValueError):
            province_id = 0
        province = provinces.filtered(lambda item: item.id == province_id)
        line_url = self._social_url(post.get("line_url"), ("line.me", "lin.ee"))
        facebook_url = self._social_url(
            post.get("facebook_url"), ("facebook.com", "fb.com", "m.me")
        )
        error = False
        if not province:
            error = "Please select a valid province."
        elif line_url is False or facebook_url is False:
            error = "Please enter valid HTTPS LINE or Facebook links."
        if schedule_error:
            error = schedule_error
        if not error:
            category_ids = []
            for category_id in request.httprequest.form.getlist("category_ids"):
                try:
                    category_ids.append(int(category_id))
                except (TypeError, ValueError):
                    continue
            values = {
                "name": (post.get("name") or "").strip(),
                "province_id": province.id,
                "district": (post.get("district") or "").strip(),
                "contact_name": (post.get("contact_name") or "").strip(),
                "working_hours": working_hours,
                "working_schedule": working_schedule,
                "contact_phone": (post.get("contact_phone") or "").strip(),
                "contact_email": (post.get("contact_email") or "").strip(),
                "website_url": (post.get("website_url") or "").strip(),
                "line_url": line_url,
                "facebook_url": facebook_url,
                "description": post.get("description") or "",
                "category_ids": [(6, 0, categories.filtered(lambda item: item.id in category_ids).ids)],
            }
            if values["name"]:
                if vendor.is_published:
                    Revision = request.env["construction.vendor.profile.revision"].sudo()
                    revision = Revision.search([("vendor_id", "=", vendor.id)], limit=1)
                    revision_values = dict(values, vendor_id=vendor.id, submitted_at=fields.Datetime.now())
                    if revision:
                        revision.write(revision_values)
                    else:
                        Revision.create(revision_values)
                    return request.redirect("/my/vendor?revision_saved=1")
                vendor.write(values)
                return request.redirect("/my/vendor?saved=1")
            error = "Company or representative name is required."
        revision = request.env["construction.vendor.profile.revision"].search(
            [("vendor_id", "=", vendor.id)], limit=1
        ) if vendor.is_published else request.env["construction.vendor.profile.revision"]
        return request.render(
            "construction_directory.portal_vendor_profile",
            {"vendor": vendor, "provinces": provinces, "categories": categories, "error": error,
             "revision": revision, "weekdays": WEEKDAYS, "schedule": schedule_form},
        )

    @http.route(
        "/my/vendor/images/save", type="http", auth="user", website=True,
        methods=["POST"], csrf=True,
    )
    def my_vendor_images_save(self, **post):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if not vendor:
            return request.not_found()
        uploads = {
            "image_1920": "image",
            "cover_image": "cover_image",
            "representative_image": "representative_image",
        }
        values = {}
        for field_name, input_name in uploads.items():
            image_data, image_error = self._read_image_upload(
                request.httprequest.files.get(input_name)
            )
            if image_error:
                return request.redirect("/my/vendor?image_error=1")
            if image_data:
                values[field_name] = image_data
        if values:
            vendor.write(values)
        return request.redirect("/my/vendor?images_saved=1")

    @http.route("/my/vendor/products", type="http", auth="user", website=True)
    def my_vendor_products(self, **kwargs):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if not vendor:
            return request.not_found()
        _provinces, categories, _province_id, _category_id = self._filters()
        products = request.env["construction.vendor.product"].search(
            [("vendor_id", "=", vendor.id)], order="sequence, name"
        )
        return request.render(
            "construction_directory.portal_vendor_products",
            {"vendor": vendor, "products": products, "categories": categories, "error": False},
        )

    @http.route(
        "/my/vendor/products/create", type="http", auth="user", website=True,
        methods=["POST"], csrf=True,
    )
    def my_vendor_product_create(self, **post):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if not vendor:
            return request.not_found()
        image_data, image_error = self._read_multiple_image_uploads("images")
        name = (post.get("name") or "").strip()
        if not name:
            error = "Please enter a product name."
        elif image_error:
            error = image_error
        elif not image_data:
            error = image_error or "Please upload a product photo."
        else:
            try:
                category_id = int(post.get("category_id") or 0)
            except (TypeError, ValueError):
                category_id = 0
            category = request.env["construction.vendor.category"].sudo().search(
                [("id", "=", category_id), ("active", "=", True)], limit=1
            )
            product = request.env["construction.vendor.product"].create(
                {
                    "vendor_id": vendor.id,
                    "name": name,
                    "category_id": category.id or False,
                    "image_1920": image_data[0],
                    "description": post.get("description") or "",
                    "price": (post.get("price") or "").strip(),
                    "is_published": vendor.is_published,
                }
            )
            if len(image_data) > 1:
                request.env["construction.vendor.product.image"].create(
                    [
                        {"product_id": product.id, "image_1920": image, "sequence": index * 10}
                        for index, image in enumerate(image_data[1:], start=1)
                    ]
                )
            return request.redirect("/my/vendor/products?created=1")
        products = request.env["construction.vendor.product"].search(
            [("vendor_id", "=", vendor.id)], order="sequence, name"
        )
        _provinces, categories, _province_id, _category_id = self._filters()
        return request.render(
            "construction_directory.portal_vendor_products",
            {"vendor": vendor, "products": products, "categories": categories, "error": error},
        )

    @http.route(
        "/my/vendor/products/<int:product_id>/save", type="http", auth="user",
        website=True, methods=["POST"], csrf=True,
    )
    def my_vendor_product_save(self, product_id, **post):
        vendor = request.env["construction.vendor"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if not vendor:
            return request.not_found()
        product = request.env["construction.vendor.product"].search(
            [("id", "=", product_id), ("vendor_id", "=", vendor.id)], limit=1
        )
        if not product:
            return request.not_found()
        values = {
            "name": (post.get("name") or "").strip(),
            "description": post.get("description") or "",
            "price": (post.get("price") or "").strip(),
        }
        try:
            category_id = int(post.get("category_id") or 0)
        except (TypeError, ValueError):
            category_id = 0
        category = request.env["construction.vendor.category"].sudo().search(
            [("id", "=", category_id), ("active", "=", True)], limit=1
        )
        values["category_id"] = category.id or False
        image_data, image_error = self._read_multiple_image_uploads("images")
        if image_error:
            products = request.env["construction.vendor.product"].search(
                [("vendor_id", "=", vendor.id)], order="sequence, name"
            )
            _provinces, categories, _province_id, _category_id = self._filters()
            return request.render(
                "construction_directory.portal_vendor_products",
                {"vendor": vendor, "products": products, "categories": categories, "error": image_error},
            )
        if product.image_count + len(image_data) > 7:
            products = request.env["construction.vendor.product"].search(
                [("vendor_id", "=", vendor.id)], order="sequence, name"
            )
            _provinces, categories, _province_id, _category_id = self._filters()
            return request.render(
                "construction_directory.portal_vendor_products",
                {"vendor": vendor, "products": products, "categories": categories,
                 "error": f"สินค้านี้มีรูปอยู่แล้ว {product.image_count} รูป เพิ่มได้อีกไม่เกิน {7 - product.image_count} รูป"},
            )
        if image_data and not product.image_1920:
            values["image_1920"] = image_data.pop(0)
        if values["name"]:
            product.write(values)
            if image_data:
                request.env["construction.vendor.product.image"].create(
                    [
                        {
                            "product_id": product.id,
                            "image_1920": image,
                            "sequence": (product.image_count + index) * 10,
                        }
                        for index, image in enumerate(image_data)
                    ]
                )
            return request.redirect("/my/vendor/products?saved=1")
        products = request.env["construction.vendor.product"].search(
            [("vendor_id", "=", vendor.id)], order="sequence, name"
        )
        _provinces, categories, _province_id, _category_id = self._filters()
        return request.render(
            "construction_directory.portal_vendor_products",
            {"vendor": vendor, "products": products, "categories": categories,
             "error": "Please enter a product name."},
        )
