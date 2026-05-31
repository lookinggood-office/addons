# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    passkey_ids = fields.One2many(
        'hr.employee.passkey', 'employee_id',
        string='Registered Passkeys',
    )
    passkey_count = fields.Integer(
        compute='_compute_passkey_count', string='Passkeys',
    )

    def _compute_passkey_count(self):
        # _read_group is the Odoo 17+ API (read_group was removed in Odoo 17)
        groups = self.env['hr.employee.passkey']._read_group(
            domain=[('employee_id', 'in', self.ids), ('active', '=', True)],
            groupby=['employee_id'],
            aggregates=['__count'],
        )
        mapping = {employee.id: count for employee, count in groups}
        for rec in self:
            rec.passkey_count = mapping.get(rec.id, 0)

    def action_register_passkey(self):
        """Open the passkey registration wizard (client action handled in JS)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'attendance_passkey_secure.register_passkey',
            'target': 'new',
            'params': {'size': 'extra-large'},
            'context': {'employee_id': self.id, 'employee_name': self.name},
        }
