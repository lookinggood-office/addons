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
        help="Products stay unpublished until the representative is approved; approved vendors' products publish immediately.",
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
            values = dict(values, is_published=all(self.mapped("vendor_id.is_published")))
        return super().write(values)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group("base.group_portal") and not self.env.user.has_group(
            "base.group_user"
        ):
            vendor_ids = {values.get("vendor_id") for values in vals_list if values.get("vendor_id")}
            vendors = self.env["construction.vendor"].browse(vendor_ids).exists()
            published_by_vendor = {vendor.id: vendor.is_published for vendor in vendors}
            vals_list = [
                dict(values, is_published=published_by_vendor.get(values.get("vendor_id"), False))
                for values in vals_list
            ]
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
    profile_revision_ids = fields.One2many(
        "construction.vendor.profile.revision", "vendor_id", string="Pending profile changes"
    )
    profile_revision_pending = fields.Boolean(
        string="Profile changes awaiting review", compute="_compute_profile_revision_pending", store=True
    )

    @api.depends("profile_revision_ids")
    def _compute_profile_revision_pending(self):
        for vendor in self:
            vendor.profile_revision_pending = bool(vendor.profile_revision_ids)
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
            if self.filtered("is_published") and set(values) - image_only_fields:
                raise AccessError("Published profile changes must be submitted for review.")
        if values.get("publication_consent"):
            values = dict(values)
            values["publication_consent_date"] = fields.Datetime.now()
        was_published = {vendor.id: vendor.is_published for vendor in self}
        result = super().write(values)
        if values.get("is_published"):
            for vendor in self.filtered(lambda item: not was_published.get(item.id)):
                vendor.product_ids.filtered("active").write({"is_published": True})
        return result


class ConstructionVendorProfileRevision(models.Model):
    _name = "construction.vendor.profile.revision"
    _description = "Pending Representative Profile Changes"
    _order = "write_date desc"

    vendor_id = fields.Many2one("construction.vendor", required=True, index=True, ondelete="cascade")
    name = fields.Char(required=True)
    province_id = fields.Many2one("res.country.state", required=True, ondelete="restrict")
    district = fields.Char()
    contact_name = fields.Char()
    working_hours = fields.Text()
    working_schedule = fields.Text()
    contact_phone = fields.Char()
    contact_email = fields.Char()
    website_url = fields.Char()
    line_url = fields.Char()
    facebook_url = fields.Char()
    description = fields.Html(sanitize=True)
    category_ids = fields.Many2many(
        "construction.vendor.category", "construction_vendor_revision_category_rel",
        "revision_id", "category_id", string="Product categories",
    )
    submitted_at = fields.Datetime(default=fields.Datetime.now, readonly=True)

    _vendor_revision_unique = models.Constraint(
        "UNIQUE(vendor_id)", "Only one pending profile revision is allowed per vendor."
    )

    def _check_reviewer(self):
        if not self.env.user.has_group("base.group_user"):
            raise AccessError("Only internal users can review profile changes.")

    def action_approve(self):
        self._check_reviewer()
        for revision in self:
            vendor = revision.vendor_id
            vendor.write({
                "name": revision.name,
                "province_id": revision.province_id.id,
                "district": revision.district,
                "contact_name": revision.contact_name,
                "working_hours": revision.working_hours,
                "working_schedule": revision.working_schedule,
                "contact_phone": revision.contact_phone,
                "contact_email": revision.contact_email,
                "website_url": revision.website_url,
                "line_url": revision.line_url,
                "facebook_url": revision.facebook_url,
                "description": revision.description,
                "category_ids": [(6, 0, revision.category_ids.ids)],
            })
        self.unlink()
        return True

    def action_reject(self):
        self._check_reviewer()
        self.unlink()
        return True
