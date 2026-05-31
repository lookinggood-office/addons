import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { runPasskeyAuthentication } from "../../services/webauthn_service";

// Odoo kiosk — robust component resolution
import PublicKioskModule from "@hr_attendance/public_kiosk/public_kiosk_app";

let kioskAttendanceApp = PublicKioskModule;
if (PublicKioskModule.kioskAttendanceApp) {
    kioskAttendanceApp = PublicKioskModule.kioskAttendanceApp;
} else if (PublicKioskModule.KioskAttendanceApp) {
    kioskAttendanceApp = PublicKioskModule.KioskAttendanceApp;
}

if (kioskAttendanceApp && kioskAttendanceApp.prototype) {
    console.log("Passkey Extension: Patching Kiosk App successfully.");
    patch(kioskAttendanceApp.prototype, {
        setup() {
            super.setup(...arguments);
            this.passkeyState = useState({ isAuthenticating: false });
        },

        async onPasskeyClick() {
            if (this.passkeyState.isAuthenticating) return;

            this.passkeyState.isAuthenticating = true;
            try {
                // 1. Run the WebAuthn ceremony (challenge fetch + credential.get)
                const serialisedCredential = await runPasskeyAuthentication();

                // 2. Complete authentication on the server (creates the attendance record)
                const result = await rpc(
                    "/attendance/passkey/authentication/complete",
                    { credential: serialisedCredential }
                );

                if (result.error) throw new Error(result.error);

                // 3. Success: Fetch full employee data and greet
                const employeeData = await rpc("/hr_attendance/attendance_employee_data", {
                    token: this.props.token,
                    employee_id: result.employee_id,
                });

                if (employeeData && employeeData.employee_name) {
                    this.employeeData = employeeData;
                    this.switchDisplay("greet");
                } else {
                    this.switchDisplay("main");
                }
            } catch (err) {
                console.error("Passkey Auth Error:", err);
                let errorMessage = "Connection Error: Please check if the device is on the same network as the server.";
                if (err.message && err.message.includes("ConnectionLost")) {
                    errorMessage = "Server unreachable. Ensure you are using the Server IP (e.g. 192.168.x.x) instead of localhost.";
                }
                alert(errorMessage);
            } finally {
                this.passkeyState.isAuthenticating = false;
            }
        },
    });
}

