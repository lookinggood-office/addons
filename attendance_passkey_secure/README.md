# Passkey Attendance (Odoo 19 Ready)

Modern, secure, and passwordless attendance tracking using WebAuthn Passkeys.

## Features
- **Biometric Check-in:** Use Fingerprint, FaceID, or Hardware Security Keys (YubiKey).
- **Secure Authentication:** Eliminates PIN sharing and "buddy punching" using cryptographic verification.
- **Kiosk Integration:** Seamlessly extends the native Odoo Attendance Kiosk.
- **Easy Registration:** Simple setup wizard for employees to register their own devices.
- **Privacy First:** No biometric data is stored on the server (handled by the browser/device).

## Installation
1. Ensure `py_webauthn` is installed in your Odoo environment:
   ```bash
   pip install py_webauthn
   ```
2. Copy the `attendance_passkey_secure` folder to your Odoo addons directory.
3. Update the Apps List and Install the module.

## Usage
1. Go to **Employees** and open an Employee profile.
2. Use the **Register Passkey** action to link a device.
3. In **Attendance Kiosk**, employees can now use the **Passkey** button to sign in/out.

## License
Licensed under LGPL-3.
