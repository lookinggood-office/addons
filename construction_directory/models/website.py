import base64

from odoo import api, models
from odoo.tools import file_open


class Website(models.Model):
    _inherit = "website"

    @api.model
    def setup_construction_directory_navigation(self):
        website = self.env.ref("website.default_website")
        with file_open("construction_directory/static/description/logo.png", "rb") as logo_file:
            logo = base64.b64encode(logo_file.read())
        with file_open("construction_directory/static/description/favicon.png", "rb") as favicon_file:
            favicon = base64.b64encode(favicon_file.read())
        website.write(
            {
                "name": "WAREHOUSE CO",
                "homepage_url": "/vendors",
                "logo": logo,
                "favicon": favicon,
            }
        )
        demo_photos = {
            "vendor_demo_bangkok_steel": (
                "steel.jpg", "Photo by Mesut Yalçın", "construction-worker-welding-steel-bars-on-building-ED2bpo7OeHg"
            ),
            "vendor_demo_chonburi_concrete": (
                "concrete.jpg", "Photo by Zane Bolen", "construction-site-with-scaffolding-and-building-materials-5oIUnZ1nPZs"
            ),
            "vendor_demo_chiangmai_roofing": (
                "roofing.jpg", "Photo by Serg Karpow", "construction-workers-installing-roof-tiles-on-a-new-building-zWL_sYw10gs"
            ),
            "vendor_demo_khonkaen_flooring": (
                "tiles.jpg", "Photo by Юлія Дубина", "a-close-up-of-a-tile-floor-UCHON6pvlmc"
            ),
            "vendor_demo_phuket_paint": (
                "paint.jpg", "Photo by Karl Solano", "paint-roller-in-white-paint-tray-eQ-8iUrb07g"
            ),
            "vendor_demo_nakhonratchasima_plumbing": (
                "plumbing.jpg", "Photo by Ryan Vargas", "a-close-up-of-pipes-and-fittings-on-a-wall-rdAKQYI3Hnk"
            ),
            "vendor_demo_songkhla_electrical": (
                "electrical.jpg", "Photo by Valentin Zickner", "electrical-wires-connected-with-yellow-terminal-blocks-zmZR_8trbE0"
            ),
            "vendor_demo_ubon_tools": (
                "tools.jpg", "Photo by Ben Spray", "workshop-tools-are-scattered-on-a-work-table-f0T-eGanP_4"
            ),
        }
        for record_id, (filename, credit, photo_slug) in demo_photos.items():
            vendor = self.env.ref(
                f"construction_directory.{record_id}", raise_if_not_found=False
            )
            if vendor:
                with file_open(
                    f"construction_directory/static/description/sample_photos/{filename}",
                    "rb",
                ) as photo_file:
                    vendor.write(
                        {
                            "image_1920": False,
                            "cover_image": base64.b64encode(photo_file.read()),
                            "image_credit": credit,
                            "image_credit_url": f"https://unsplash.com/photos/{photo_slug}",
                        }
                    )
        website.company_id.write({"phone": False})
        menus = self.env["website.menu"].search([("website_id", "=", website.id)])
        register_menu = menus.filtered(lambda menu: menu.url == "/vendors/register")
        register_menu.with_context(adding_designer_group_to_menu=True).write(
            {"group_ids": [(6, 0, [self.env.ref("base.group_public").id])]}
        )
        menus.filtered(
            lambda menu: menu.parent_id == website.menu_id and menu.url == "/"
        ).unlink()
        menus = self.env["website.menu"].search([("website_id", "=", website.id)])
        for menu in menus:
            if menu.url == "/contactus":
                menu.write({"name": "ติดต่อเรา"})
