{
    'name': 'User to Portal Action (Odoo 19)',
    'summary': 'Bulk convert Internal Users to Portal with admin safety protection',
    'description': """
    Convert Internal Users to Portal Action
    =======================================
    Adds a convenient menu item in the User action menu to convert selected internal users to the Portal group.
    It includes built-in safety checks to skip the main Administrator and any users with Administrative rights.
    """,
    'author': 'LookingGood Co.,Ltd.',
    'website': 'lookinggood.odoo.com',
    'category': 'Extra Tools',
    'version': '19.0.1.3',
    'depends': ['base'],
    'data': [
        'data/server_action.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
