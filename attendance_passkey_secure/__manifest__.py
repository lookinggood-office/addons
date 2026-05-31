{
    'name': 'Passkey Attendance',
    'summary': 'Secure & Professional Passwordless Biometric Check-in (Passkeys)',
    'description': """
    Passkey Attendance
    ==================
    Upgrade your Odoo Attendance Kiosk with modern WebAuthn Passkey technology.
    
    Key Features:
    - One-click Biometric Check-in (FaceID, Fingerprint, YubiKey)
    - Zero-Password environment for maximum security
    - Prevention of "Buddy Punching" via cryptographic hardware binding
    - Native Odoo 19 Kiosk integration
    - Streamlined Employee self-registration
    """,
    'author': 'LKG Team',
    'website': 'lkgood.odoo.com',
    'category': 'Human Resources/Attendances',
    'version': '19.0.1.0',
    'depends': ['hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
    ],
    'assets': {
        'hr_attendance.assets_public_attendance': [
            'attendance_passkey_secure/static/src/scss/passkey_kiosk.scss',
            'attendance_passkey_secure/static/src/js/services/webauthn_service.js',
            'attendance_passkey_secure/static/src/js/components/passkey_kiosk_extension/passkey_kiosk_extension.js',
            'attendance_passkey_secure/static/src/js/components/passkey_kiosk_extension/passkey_kiosk_extension.xml',
        ],
        'web.assets_backend': [
            'attendance_passkey_secure/static/src/js/services/webauthn_service.js',
            'attendance_passkey_secure/static/src/js/components/passkey_register_wizard/passkey_register_wizard.js',
            'attendance_passkey_secure/static/src/js/components/passkey_register_wizard/passkey_register_wizard.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
