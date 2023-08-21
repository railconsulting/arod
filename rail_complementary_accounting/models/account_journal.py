# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    complementary_account_id = fields.Many2one('account.account', string="Cuenta complementaria")
    complementary_currency_id = fields.Many2one('res.currency',string="Moneda complementaria")
