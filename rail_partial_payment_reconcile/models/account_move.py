# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def js_partial_button(self, line_id):
        return {
            'name': _('Partial Register Payment'),
            'res_model': 'partial.payment.wizard',
            'view_mode': 'form',
            'context': {
                'line_id': line_id,
                'move_id': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
