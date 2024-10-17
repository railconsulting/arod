# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CrediApprovalWiz(models.TransientModel):
    _name = 'credit.approval.wizard'
    _description = 'Credit Approval flow'

    order_id = fields.Many2one('sale.order')
    partner_credit_warning = fields.Text('Description')

    def request_approval(self):
        self.order_id.write({
            'state': 'to approve',
        })
        return{
            'effect':{
                'fadeout':'slow',
                'message':'Ya puedes solicitar la aprobacion',
                'type':'rainbow_man',
            }
        }
