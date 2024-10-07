# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError
from collections import defaultdict
import xlsxwriter, io, base64, logging
from datetime import datetime

_logger = logging.getLogger(__name__)



class SaleProfitReportLine(models.TransientModel):
    _name = 'sale.profit.report.line'
    _description = 'Sale Profit Report Line'

    wizard_id = fields.Many2one('sale.profit.report', string='Report')
    move_id = fields.Many2one('account.move', string="Folio")
    move_line_ids = fields.Char("Apuntes contables")
    refund_ids = fields.Char("Devoluciones")
    bonification_ids = fields.Char("Bonificaciones")
    cost_ids = fields.Char("Costos")
    free_delivery_ids = fields.Char("Entrega gratuita")
    customer_delivery_ids = fields.Char("Entrega cliente")
    c0 = fields.Char(string="Folio")
    c1 = fields.Char(string="Comentario")
    c2 = fields.Date(string="Fecha")
    c3 = fields.Char(string="Cliente")
    c4 = fields.Char(string="Factura / Ref")
    c5 = fields.Float(string="Costo")
    c6 = fields.Float(string="Sub-Total")
    c7 = fields.Float(string="%")
    c8 = fields.Float(string="Flete")
    c9 = fields.Float(string="Costo Ctrl")
    c10 = fields.Float(string="Sub-Total")
    c11 = fields.Float(string="%")
    c12 = fields.Float(string="Devs. Costo")
    c13 = fields.Float(string="Devs. Sub-Total")
    c14 = fields.Float(string="Devs. Costo Neto")
    c15 = fields.Float(string="Devs. Sub-Neto")
    c16 = fields.Float(string="Devs. %")
    c17 = fields.Float(string="Bonif. Sub-Total")
    c18 = fields.Float(string="Bonif. Costo")
    c19 = fields.Float(string="Bonif. Sub-Neto")
    c20 = fields.Float(string="Bonif. %")
    c21 = fields.Float(string="CTRL-1")
    c22 = fields.Float(string="CTRL-2")
    c23 = fields.Float(string="SUB-TOTAL")
    c24 = fields.Float(string="IMPUESTO")
    c25 = fields.Float(string="NETO")
    c26 = fields.Float(string="COSTO")
    c27 = fields.Float(string="U. BRUTA")
    c28 = fields.Float(string="% TOTAL")


    def open_invoice_cost_docs(self):
        """ Open documents related to the invoice cost """
        stock_valuation_layers = self.env['stock.valuation.layer'].search([
            ('product_id', 'in', self.move_id.line_ids.mapped('product_id').ids),
        ])

        return {
            'name': 'Related Documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.valuation.layer',
            'domain': [('id', 'in', stock_valuation_layers.ids)],
            'target': 'current',
        }

    def open_invoice_subtotal_docs(self):
        """ Open documents related to the invoice subtotal """
        # Logic to fetch related documents based on invoice subtotal
        account_moves = self.env['account.move'].search([
            ('id', '=', self.move_id.id),
        ])

        return {
            'name': 'Related Documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', account_moves.ids)],
            'target': 'current',
        }

    def open_nc_subtotal_docs(self):
        """ Open documents related to the NC (Credit Note) subtotal """
        account_moves = self.env['account.move'].search([
            ('reversed_entry_id', '=', self.move_id.id),
        ])

        return {
            'name': 'Related Documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', account_moves.ids)],
            'target': 'current',
        }

    def open_bonus_subtotal_docs(self):
        """ Open documents related to the bonus subtotal """
        account_moves = self.env['account.move'].search([
            ('reversed_entry_id', '=', self.move_id.id),
        ])

        return {
            'name': 'Related Documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', account_moves.ids)],
            'target': 'current',
        }

    def open_total_profit_docs(self):
        """ Open documents related to the total profit """
        account_moves = self.env['account.move'].search([
            ('id', '=', self.move_id.id),
        ])

        return {
            'name': 'Related Documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', account_moves.ids)],
            'target': 'current',
        }
    
    def open_free_delivery_docs(self):
        """ Open documents related to free delivery """
        sale_orders = self.env['sale.order'].search([
            ('order_line', 'in', self.move_id.line_ids.sale_line_ids.ids),
            ('shipping_type', '=', 'free'),
        ])

        return {
            'name': 'Related Free Delivery Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', 'in', sale_orders.ids)],
            'target': 'current',
        }

    def open_total_delivery_docs(self):
        """ Open documents related to total delivery (free + customer) """
        sale_orders = self.env['sale.order'].search([
            ('order_line', 'in', self.move_id.line_ids.sale_line_ids.ids),
            '|',
            ('shipping_type', '=', 'free'),
            ('shipping_type', '=', 'customer'),
        ])

        return {
            'name': 'Related Total Delivery Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', 'in', sale_orders.ids)],
            'target': 'current',
        }


