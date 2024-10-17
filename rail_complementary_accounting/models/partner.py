# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResParter(models.Model):
    _inherit='res.partner'

    property_complementary_account_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Payable",
        domain="[('account_type', '=', 'liability_current'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=True)