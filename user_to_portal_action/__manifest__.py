{
    'name': 'PortalSwift',
    'summary': 'Fast & Secure Bulk User-to-Portal Conversion',
    'description': """
    Swift Portalize
    ===============
    Professional utility to convert internal users to the Portal group instantly.
    Features:
    - One-click bulk conversion from List View
    - Smart Admin Shield to protect system managers
    - Native Odoo 19 field support (group_ids)
    - Zero-config deployment
    """,
    'author': 'LookingGood Co.,Ltd.',
    'website': 'lookinggood.odoo.com',
    'category': 'Extra Tools',
    'version': '19.0.1.3',
    'depends': ['base'],
    'data': [
        'data/server_action.xml',
    ],
    'images': [
        'static/description/banner.svg',
        'static/description/icon.svg',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
