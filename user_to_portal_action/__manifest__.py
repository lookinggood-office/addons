{
    'name': 'User2Portal Action',
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
    'author': 'LKG Team',
    'website': 'lkgood.odoo.com',
    'category': 'Extra Tools',
    'version': '19.0.1.4',
    'depends': ['base'],
    'data': [
        'security/security_data.xml',
        'data/server_action.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
