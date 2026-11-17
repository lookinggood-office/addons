from . import controllers
from . import models


def post_init_hook(env):
    website = env.ref("website.default_website")
    root_menu = website.menu_id
    menu_model = env["website.menu"]
    menu_model.search(
        [
            ("website_id", "=", website.id),
            ("parent_id", "=", root_menu.id),
            ("url", "=", "/"),
        ]
    ).unlink()
    menu_model.search(
        [("website_id", "=", website.id), ("url", "=", "/contactus")]
    ).write({"name": "ติดต่อเรา"})
    for menu in root_menu.child_id:
        if menu.url == "/":
            menu.write({"name": "หน้าแรก"})
        elif menu.url == "/contactus":
            menu.write({"name": "ติดต่อเรา"})
    menu_items = [
        ("ค้นหาตัวแทน", "/vendors", 20),
        ("ลงทะเบียนตัวแทน", "/vendors/register", 30),
    ]
    for name, url, sequence in menu_items:
        if not menu_model.search(
            [("website_id", "=", website.id), ("url", "=", url)], limit=1
        ):
            menu_values = {
                    "name": name,
                    "url": url,
                    "parent_id": root_menu.id,
                    "website_id": website.id,
                    "sequence": sequence,
                }
            if url == "/vendors/register":
                menu_values["group_ids"] = [(6, 0, [env.ref("base.group_public").id])]
            menu_model.create(menu_values)
