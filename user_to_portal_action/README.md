# User to Portal Action (Odoo 19)

Easily convert Internal Users to Portal Users via the Action menu in Odoo 19.

## Features
- **Bulk Conversion:** Convert multiple users at once from the Users list view.
- **Safety First:** Automatically skips Administrator (ID 1) and users with 'Administration / Settings' rights to prevent system lockouts.
- **Clean Group Management:** Replaces all internal groups with the Portal group in one click.
- **User Notifications:** Provides clear feedback on how many users were successfully converted.
- **Odoo 19 Ready:** Uses the latest `group_ids` field and client action notifications.

## Installation
1. Copy the `user_to_portal_action` folder to your Odoo addons directory.
2. Update the Apps List in Odoo.
3. Install the module.

## Usage
1. Go to **Settings > Users & Companies > Users**.
2. Select the users you want to convert.
3. Click on the **Action** button and select **Convert to Portal User**.

## License
Licensed under LGPL-3.
