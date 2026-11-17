from urllib.parse import urlparse

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ConstructionVendorCategory(models.Model):
    _name = "construction.vendor.category"
    _description = "Construction Material Category"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    image_1920 = fields.Image(string="Category cover", max_width=1920, max_height=1920)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class ConstructionVendorProduct(models.Model):
    _name = "construction.vendor.product"
    _description = "Construction Vendor Product"
    _order = "sequence, name"

    name = fields.Char(string="Product name", required=True)
    vendor_id = fields.Many2one(
        "construction.vendor", string="Vendor", required=True, index=True, ondelete="cascade"
    )
    category_id = fields.Many2one("construction.vendor.category", string="Category")
    image_1920 = fields.Image(string="Product photo", max_width=1920, max_height=1920)
    image_ids = fields.One2many(
        "construction.vendor.product.image", "product_id", string="Additional product photos"
    )
    image_count = fields.Integer(string="Photo count", compute="_compute_image_count")
    description = fields.Html(string="Product details", sanitize=True)
    price = fields.Char(string="Price / price note")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    is_published = fields.Boolean(
        string="Published", default=True,
        help="Products from approved representatives are published immediately.",
    )

    @api.depends("image_1920", "image_ids")
    def _compute_image_count(self):
        for product in self:
            product.image_count = (1 if product.image_1920 else 0) + len(product.image_ids)

    def write(self, values):
        if self.env.user.has_group("base.group_portal") and not self.env.user.has_group(
            "base.group_user"
        ):
            allowed_fields = {"name", "category_id", "image_1920", "description", "price"}
            if set(values) - allowed_fields:
                raise AccessError("Portal users may only update their own product details.")
            values = dict(values, is_published=True)
        return super().write(values)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group("base.group_portal") and not self.env.user.has_group(
            "base.group_user"
        ):
            vals_list = [dict(values, is_published=True) for values in vals_list]
        return super().create(vals_list)


class ConstructionVendorProductImage(models.Model):
    _name = "construction.vendor.product.image"
    _description = "Construction Vendor Product Photo"
    _order = "sequence, id"

    product_id = fields.Many2one(
        "construction.vendor.product", required=True, index=True, ondelete="cascade"
    )
    image_1920 = fields.Image(string="Product photo", required=True, max_width=1920, max_height=1920)
    sequence = fields.Integer(default=10)

    @api.constrains("product_id")
    def _check_photo_limit(self):
        for photo in self:
            product = photo.product_id
            if (1 if product.image_1920 else 0) + len(product.image_ids) > 7:
                raise ValidationError("A product can have at most 7 photos.")


class ConstructionVendor(models.Model):
    _name = "construction.vendor"
    _description = "Construction Material Representative"
    _order = "featured desc, sequence, name"

    name = fields.Char(string="Company / representative name", required=True)
    user_id = fields.Many2one(
        "res.users", string="Portal account", copy=False, index=True, ondelete="set null"
    )
    product_ids = fields.One2many("construction.vendor.product", "vendor_id", string="Products")
    public_product_ids = fields.One2many(
        "construction.vendor.product", "vendor_id", string="Published products",
        domain=[("active", "=", True), ("is_published", "=", True)],
    )
    image_1920 = fields.Image(string="Company logo", max_width=1920, max_height=1920)
    cover_image = fields.Image(string="Company cover photo", max_width=1920, max_height=1920)
    representative_image = fields.Image(string="Representative photo", max_width=1920, max_height=1920)
    image_credit = fields.Char(string="Photo credit")
    image_credit_url = fields.Char(string="Photo source URL")
    province_id = fields.Many2one(
        "res.country.state",
        string="Province",
        required=True,
        domain=[("country_id.code", "=", "TH")],
        ondelete="restrict",
    )
    district = fields.Char(string="District / area")
    street = fields.Char(string="Address")
    zip = fields.Char(string="Postal code")
    category_ids = fields.Many2many(
        "construction.vendor.category",
        "construction_vendor_category_rel",
        "vendor_id",
        "category_id",
        string="Product categories",
    )
    description = fields.Html(string="Company profile", sanitize=True)
    contact_name = fields.Char(string="Contact person")
    working_hours = fields.Text(string="Business / contact hours")
    working_schedule = fields.Text(string="Structured business hours", copy=False)
    contact_phone = fields.Char(string="Phone")
    contact_email = fields.Char(string="Email")
    website_url = fields.Char(string="Website")
    line_url = fields.Char(string="LINE profile URL")
    facebook_url = fields.Char(string="Facebook page URL")
    publication_consent = fields.Boolean(string="Consent to publish contact details")
    publication_consent_date = fields.Datetime(
        string="Publication consent date", readonly=True, copy=False
    )
    featured = fields.Boolean(string="Featured")
    is_sponsored = fields.Boolean(
        string="Recommended representative",
        help="Show this approved listing in the recommended representatives section during the selected dates.",
    )
    sponsor_start = fields.Date(string="Recommendation starts")
    sponsor_end = fields.Date(string="Recommendation ends")
    is_published = fields.Boolean(
        string="Published",
        default=False,
        help="Only approved and published listings appear on the public website.",
    )
    sequence = fields.Integer(default=10)

    @api.constrains("line_url", "facebook_url")
    def _check_social_urls(self):
        allowed_domains = {
            "line_url": ("line.me", "lin.ee"),
            "facebook_url": ("facebook.com", "fb.com", "m.me"),
        }
        for vendor in self:
            for field_name, domains in allowed_domains.items():
                value = (vendor[field_name] or "").strip()
                if not value:
                    continue
                parsed = urlparse(value)
                hostname = (parsed.hostname or "").lower()
                if parsed.scheme != "https" or not any(
                    hostname == domain or hostname.endswith("." + domain)
                    for domain in domains
                ):
                    raise ValidationError("Please enter a valid HTTPS LINE or Facebook URL.")

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get("publication_consent") and not values.get("publication_consent_date"):
                values["publication_consent_date"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, values):
        if self.env.user.has_group("base.group_portal") and not self.env.user.has_group(
            "base.group_user"
        ):
            allowed_fields = {
                "name", "image_1920", "cover_image", "representative_image",
                "working_hours", "working_schedule", "province_id", "district", "street", "zip",
                "category_ids", "description", "contact_name", "contact_phone",
                "contact_email", "website_url", "line_url", "facebook_url",
            }
            if set(values) - allowed_fields:
                raise AccessError("Portal users may only update their own public profile fields.")
            image_only_fields = {"image_1920", "cover_image", "representative_image"}
            if set(values) - image_only_fields:
                values = dict(values, is_published=False)
        if values.get("publication_consent"):
            values = dict(values)
            values["publication_consent_date"] = fields.Datetime.now()
        return super().write(values)
