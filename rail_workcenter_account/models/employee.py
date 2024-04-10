# -*- coding: utf-8 -*-

from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    inventory_account_id = fields.Many2one('account.account', string="Cuenta produccion en proceso", required=True)
    expense_account_id = fields.Many2one('account.account', string="Cuenta gasto", required=True)
