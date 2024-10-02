# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('account_id')
    def _get_group_id(self):
        for r in self:
            if r.account_id:
                r.update({
                    'group_id': r.account_id.group_id.id
                })
    group_id = fields.Many2one('account.group', compute='_get_group_id', store=True)