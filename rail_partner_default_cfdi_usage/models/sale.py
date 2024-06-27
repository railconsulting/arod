# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        vals = super(SaleOrder,self)._prepare_invoice()
        vals["l10n_mx_edi_usage"] = self.partner_invoice_id.uso_cfdi
        return vals