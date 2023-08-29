# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        msg = "No puedes validar la entrega debido a que las siguientes facturas no tienen pago: \n"
        _logger.critical("Si entro")
        if self.sale_id:
            if not self.sale_id.invoice_ids:
                block_invoices = self.sale_id.payment_term_id.stock_payment_val
                if block_invoices:
                    raise ValidationError("Este despacho aun no tiene facturas y pagos asociados\n"+
                                          "Para continuar registra la factura y el pago correspondiente")
            else:
                block_invoices = self.sale_id.invoice_ids.filtered(lambda x: 
                    x.invoice_payment_term_id.stock_payment_val
                    and x.amount_residual > 0
                )
                if block_invoices:
                    for i in block_invoices:
                        msg += i.name +"\n"                
                    raise ValidationError(msg)
        return res