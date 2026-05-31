# -*- coding: utf-8 -*-
from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    check_in_method = fields.Selection(
        selection=[
            ('manual', 'Manual'),
            ('passkey', 'Passkey'),
            ('rfid', 'RFID'),
        ],
        string='Check-in Method',
        default='manual',
        readonly=True,
    )
