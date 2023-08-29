# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    stock_payment_val = fields.Boolean("Bloquear despacho")