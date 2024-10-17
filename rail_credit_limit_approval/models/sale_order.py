# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, RedirectWarning

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection=[
            ('draft', "Quotation"),
            ('sent', "Quotation Sent"),
            ('to approve', "To Approve"),
            ('sale', "Sales Order"),
            ('done', "Locked"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    
    credit_limit_restriction = fields.Boolean(compute='_compute_credit_limit_restriction')

    @api.depends('partner_credit_warning','partner_id','partner_id.use_partner_credit_limit')
    def _compute_credit_limit_restriction(self):
        for r in self:
            restriction = False
            if len(r.partner_credit_warning.replace(' ','')) > 0 and r.partner_id.use_partner_credit_limit:
                restriction = True
            r.credit_limit_restriction = restriction