# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ReporteKardex(models.AbstractModel):
    _name = 'report.kardex.reporte_kardex'

    def get_initial(self, data, locations):
        self.env.cr.execute('''
            select sum(qty_in) as in, sum(qty_out) as out, product_id 
            from ( 
                    select sum(product_qty) as qty_in, 0 as qty_out, product_id
                    from stock_move
                    where state = 'done' and product_id = %s and location_dest_id in %s and date <= %s 
                    group by product_id 
                    
                    union 
               
                    select 0 as qty_in, sum(product_qty) as qty_out, product_id 
                    from stock_move 
                    where state = 'done' and product_id = %s and  location_id in %s and date <= %s 
                    group by product_id 
                ) movimientos
            group by product_id''',
            (data['product_id'], tuple(locations), data['date_from'], data['product_id'], tuple(locations), data['date_from']))
        lines = self.env.cr.dictfetchall()

        total = 0
        for l in lines:
            total += l['in'] - l['out']

        return total

    def get_lines(self, datos, product_ids):
        totals = {}
        totals['in'] = 0
        totals['out'] = 0
        totals['initial'] = 0
        totals['warehouse_id'] = False

        product = self.env['product.product'].browse([product_ids])
        lines = []

        locations = datos['location_ids'].ids
        #_logger.critical("UBICACION: " + str(location))
        dict = {'product_id': product.id, 
                'date_from': datos['date_from']
            }

        totals['init'] = self.get_initial(dict, locations)

        balance = totals['init']
        moves = self.env['stock.move'].search(
            [
                ('product_id','=',product.id), 
                ('date','>=',datos['date_from']), 
                ('date','<=',datos['date_to']), 
                ('state','=','done'), 
                '|', ('location_id','in', locations), ('location_dest_id','in', locations)
            ], order = 'date')
        #_logger.critical("MOVE: " + str(moves))
        if moves:
            for m in moves:
                detail = {
                    'company':'-',
                    'uom': m.product_id.uom_id.name,
                    'location': False,
                    'date': m.date,
                    'in': 0,
                    'out': 0,
                    'balance':balance
                }

                if m.picking_id:
                    detail['document'] = m.picking_id.name
                    if m.picking_id.partner_id:
                        detail['company'] = m.picking_id.partner_id.name

                else:
                    detail['document'] = m.name
        
                if m.location_dest_id.id in locations:
                    detail['type'] = 'Ingreso'
                    detail['location'] = m.location_dest_id.display_name
                    detail['in'] = m.product_qty
                    totals['in'] += m.product_qty
                elif m.location_id.id in locations:
                    detail['type'] = 'Salida'
                    detail['location'] = m.location_id.display_name
                    detail['out'] = -m.product_qty
                    totals['out'] -= m.product_qty

                balance += detail['in'] + detail['out']
                detail['balance'] = balance
                cost = m.price_unit
                detail['cost'] = cost
                detail['order_id'] = m.sale_line_id.order_id.name if m.sale_line_id else ''
                detail['invoice_id'] = m.sale_line_id.invoice_lines[0].move_id.name if m.sale_line_id and m.sale_line_id.invoice_lines else ''
                if not detail['order_id']:
                    try:
                        detail['order_id'] = m.purchase_line_id.order_id.name if m.purchase_line_id else '-'
                        detail['invoice_id'] = m.purchase_line_id.invoice_lines[0].move_id.name if m.purchase_line_id and m.purchase_line_id.invoice_lines else '-'
                    except:
                        pass
                lines.append(detail)
        lines = sorted(lines, key=lambda x: x['date'])

        return {'product': product.name, 'lines': lines, 'totals': totals}
