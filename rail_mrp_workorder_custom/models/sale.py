# -*- coding: utf-8 -*-

from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shipping_type = fields.Selection(string="Tipo envio", selection=[('none','No aplica'),('free','Gratis'),('customer','Cliente')], default='none')
    shipping_total = fields.Float("Total envio")

class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    def button_confirm(self):
        res = super(ChooseDeliveryCarrier, self).button_confirm()
        if self.delivery_price > 0:
            self.order_id.write({
                'shipping_type': 'customer',
                'shipping_total': self.display_price
            })
        else:
            self.order_id.write({
                'shipping_type': 'free',
                'shipping_total': self.display_price
            })
        
        return res