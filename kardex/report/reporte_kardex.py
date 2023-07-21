# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ReporteKardex(models.AbstractModel):
    _name = 'report.kardex.reporte_kardex'

    def inicial(self, datos):
        self.env.cr.execute('''
            select sum(qty_in) as entrada, sum(qty_out) as salida, product_id 
            from ( 
                    select sum(product_qty) as qty_in, 0 as qty_out, product_id
                    from stock_move
                    where state = 'done' and product_id = %s and location_dest_id = %s and date <= %s 
                    group by product_id 
                    
                    union 
               
                    select 0 as qty_in, sum(product_qty) as qty_out, product_id 
                    from stock_move 
                    where state = 'done' and product_id = %s and  location_id = %s and date <= %s 
                    group by product_id 
                ) movimientos
            group by product_id''',
            (datos['product_id'], datos['location_id'], datos['date_from'], datos['product_id'], datos['location_id'], datos['date_from']))
        lineas = self.env.cr.dictfetchall()

        total = 0
        for l in lineas:
            total += l['entrada'] - l['salida']

        return total

    def lineas(self, datos, product_ids):
        totales = {}
        totales['entrada'] = 0
        totales['salida'] = 0
        totales['inicio'] = 0
        totales['warehouse_id'] = False

        producto = self.env['product.product'].browse([product_ids])
        #raise ValidationError(str(datos['ubicacion_ids']))
        lineas = []
        for location in datos['ubicacion_ids']:
            #_logger.critical("UBICACION: " + str(location))
            dict = {'product_id': producto.id, 
                    'location_id': location.id, 
                    'date_from': datos['date_from']
                }

            totales['inicio'] = self.inicial(dict)

            saldo = totales['inicio']
            moves = self.env['stock.move'].search(
                [
                    ('product_id','=',producto.id), 
                    ('date','>=',datos['date_from']), 
                    ('date','<=',datos['date_to']), 
                    ('state','=','done'), 
                    '|', ('location_id','=', location.id), ('location_dest_id','=', location.id)
                ], order = 'date')
            #_logger.critical("MOVE: " + str(moves))
            if moves:
                for m in moves:
                    detalle = {
                        'empresa':'-',
                        'unidad_medida': m.product_id.uom_id.name,
                        'location': False,
                        'fecha': m.date,
                        'entrada': 0,
                        'salida': 0,
                        'saldo':saldo
                    }

                    if m.picking_id:
                        detalle['documento'] = m.picking_id.name
                        if m.picking_id.partner_id:
                            detalle['empresa'] = m.picking_id.partner_id.name

                    else:
                        detalle['documento'] = m.name
            
                    
                    if m.location_dest_id.id == location.id:
                        detalle['tipo'] = 'Ingreso'
                        detalle['location'] = location.display_name
                        detalle['entrada'] = m.product_qty
                        totales['entrada'] += m.product_qty
                    elif m.location_id.id == location.id:
                        detalle['tipo'] = 'Salida'
                        detalle['location'] = location.display_name
                        detalle['salida'] = -m.product_qty
                        totales['salida'] -= m.product_qty

                    saldo += detalle['entrada']+detalle['salida']
                    detalle['saldo'] = saldo
                    totales['warehouse_id'] = location.warehouse_id.display_name
                    costo = m.price_unit
                    detalle['costo'] = costo
                    detalle['order_id'] = m.sale_line_id.order_id.name if m.sale_line_id else ''
                    detalle['invoice_id'] = m.sale_line_id.invoice_lines[0].move_id.name if m.sale_line_id and m.sale_line_id.invoice_lines else ''
                    if not detalle['order_id']:
                        try:
                            detalle['order_id'] = m.purchase_line_id.order_id.name if m.purchase_line_id else '-'
                            detalle['invoice_id'] = m.purchase_line_id.invoice_lines[0].move_id.name if m.purchase_line_id and m.purchase_line_id.invoice_lines else '-'
                        except:
                            pass
                    lineas.append(detalle)
            #else:
            #    raise ValidationError("No se encuentra ningun movimiento en ninguna ubicacion seleccionada")

        return {'producto': producto.name, 'lineas': lineas, 'totales': totales}

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        return  {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
        }
    
    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        return  {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
        }
