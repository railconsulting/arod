# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import datetime, base64, io, logging, xlsxwriter

_logger = logging.getLogger(__name__)


class AsistenteKardex(models.TransientModel):
    _name = 'asistente.kardex'
    _description = 'Kardex'



    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id.id, required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', string="Almacen")
    #ubicacion_id = fields.Many2one("stock.location", string="Ubicacion", required=True)
    location_ids = fields.Many2many("stock.location", string="Ubicaciones")
    product_ids = fields.Many2many("product.product", string="Productos", domain=[('detailed_type','in',['consu','product'])])
    date_from = fields.Datetime(string="Fecha Inicial" )
    date_to = fields.Datetime(string="Fecha Final")
    xls_file = fields.Binary(string="Data")
    name = fields.Char(string='File Name', readonly=True)

    @api.onchange('warehouse_ids')
    def onchange_warehouse_ids(self):
        if self.warehouse_ids:
            self.location_ids = False

    def check_date_range(self):
        if self.end_date < self.start_date:
            raise ValidationError(_('Ingresa un rango de fechas apropiado'))

    def print_report(self):
        data = {
             'ids': [],
             'model': 'asistente.kardex',
             'form': self.read()[0]
        }
        return self.env.ref('kardex.action_reporte_kardex').report_action(self, data=data)
    
    def get_location(self):
        stock_ids = []
        location_obj = self.env['stock.location']
        domain = [('company_id', '=', self.company_id.id), ('usage', '=', 'internal')]
        if self.warehouse_ids and not self.location_ids:
            for warehouse in self.warehouse_ids:
                stock_ids.append(warehouse.view_location_id.id)
            domain.append(('location_id', 'child_of', stock_ids))
        elif self.location_ids:
            for location in self.location_ids:
                if location.child_ids:
                    domain.append(('location_id','child_of', location.id))
                else:
                    domain.append(('location_id','=', location.id))

        final_stock_ids = location_obj.search(domain)
        _logger.critical(str(final_stock_ids))
        return final_stock_ids

    def _xlsx_kardex(self):
        company = self.company_id
        f = io.BytesIO()
        xls_filename = "Kardex " + self.env.company.name + " " + str(self.date_from.strftime('%d/%m/%Y')) + "_" + str(self.date_to.strftime('%d/%m/%Y'))
        book = xlsxwriter.Workbook(f)
        sheet = book.add_worksheet('Kardex')
        main_header = book.add_format({
            'bold':True,
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Calibri',
            'font_size': 18,
        })

        datos = {}
        datos['date_from'] = self.date_from
        datos['date_to'] = self.date_to
        #locations = self.location_ids if self.location_ids else self.get_location()
        locations = self.get_location()
        datos['ubicacion_ids'] = locations
        
        row = 2
        if self.product_ids:
            products = self.product_ids
        else:
            products = self.env['product.product'].search()

        for p in products:
            result = self.env['report.kardex.reporte_kardex'].lineas(datos, p.id)

            sheet.write(row, 0, 'Fecha desde:')
            sheet.write(row, 1, 'Fecha hasta:')
            sheet.write(row, 2, 'Almacen:')
            sheet.write(row, 3, 'Producto:')
            row += 1
            sheet.write(row, 0, datetime.datetime.strftime(self.date_from,'%d/%m/%Y'))
            sheet.write(row, 1, datetime.datetime.strftime(self.date_to,'%d/%m/%Y'))

            sheet.write(row, 2, result['totales']['warehouse_id'])
            sheet.write(row, 3, p.name)
            row += 1
            sheet.write(row, 0, 'Inicial:')
            sheet.write(row, 1, 'Entradas:')
            sheet.write(row, 2, 'Salidas:')
            sheet.write(row, 3, 'Final:')
            row += 1
            sheet.write(row, 0, result['totales']['inicio'])
            sheet.write(row, 1, result['totales']['entrada'])
            sheet.write(row, 2, result['totales']['salida'])
            sheet.write(row, 3, result['totales']['inicio']+result['totales']['entrada']+result['totales']['salida'])
            row += 2
            sheet.write(row, 0, 'Fecha')
            sheet.write(row, 1, 'Documento')
            sheet.write(row, 2, '#Sale / #Purchase')
            sheet.write(row, 3, '# Invoice')
            sheet.write(row, 4, 'Empresa')
            sheet.write(row, 5, 'Tipo')
            sheet.write(row, 6, 'UOM')
            sheet.write(row, 7, 'Ubicacion')
            sheet.write(row, 8, 'Entradas')
            sheet.write(row, 9, 'Salidas')
            sheet.write(row, 10, 'Final')
            sheet.write(row, 11, 'Costo')
            sheet.write(row, 12, 'Total')
            row += 1
            for linea in result['lineas']:
                sheet.write(row, 0, datetime.datetime.strftime(linea['fecha'],'%d/%m/%Y'))
                sheet.write(row, 1, linea['documento'])
                sheet.write(row, 2, linea['order_id'])
                sheet.write(row, 3, linea['invoice_id'])
                sheet.write(row, 4, linea['empresa'])
                sheet.write(row, 5, linea['tipo'])
                sheet.write(row, 6, linea['unidad_medida'])
                sheet.write(row, 7, linea['location'])
                sheet.write(row, 8, linea['entrada'])
                sheet.write(row, 9, abs(linea['salida']))
                sheet.write(row, 10, linea['saldo'])
                sheet.write(row, 11, linea['costo'])
                sheet.write(row, 12, linea['saldo'] * linea['costo'])
                row += 1
            row += 1

        book.close()
        self.write({
            'xls_file': base64.encodebytes(f.getvalue()),
            'name': xls_filename + ".xlsx"
        })

    def click_button(self):
        self._xlsx_kardex()
        return {
            'name': 'Same title',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    """ def reporte_tree_view(self):
        self.env['kardex.asistente_kardex.custom.report'].search([]).unlink()
        datos = {}
        datos['date_from'] = self.date_from
        datos['date_to'] = self.date_to
        datos['ubicacion_id'] = []
        datos['ubicacion_id'].append(self.ubicacion_id.id)
        for producto in self.product_ids:
            resultado = self.env['report.kardex.reporte_kardex'].lineas(datos, producto.id)
            for linea in resultado['lineas']:
                vals = {
                    'date' : linea['fecha'],
                    'documents' : linea['documento'],
                    'order_ref' : linea['order_id'],
                    'invoice_ref' : linea['invoice_id'],
                    'partner_name' : linea['empresa'],
                    'tipo' : linea['tipo'],
                    'uom' : linea['unidad_medida'],
                    'qty1' : linea['entrada'],
                    'qty2' : abs(linea['salida']),
                    'saldo' : linea['saldo'],
                    'cost' : linea['costo'],
                    'total' : linea['saldo'] + linea['costo'],
                }
                self.env['asistente.kardex.custom.report'].create(vals)
        return {
            'name': _('Kardex Report'),
            'view_mode': 'tree',
            'res_model': 'kardex.asistente_kardex.custom.report',
            'type': 'ir.actions.act_window',
        } """

""" class AsistenteKardexCustomReport(models.TransientModel):
    _name = 'kardex.asistente_kardex.custom.report'
    _description = 'Kardex Custom Report'

    date = fields.Datetime(string="Fecha")
    documents = fields.Char(string="Documento")
    order_ref = fields.Char(string="#Sale / #Purchase")
    invoice_ref = fields.Char(string="# Invoice")
    partner_name = fields.Char(string="Empresa")
    tipo = fields.Char(string="Tipo")
    uom = fields.Char(string="UOM")
    qty1 = fields.Char(string="Entradas")
    qty2 = fields.Char(string="Salidas")
    saldo = fields.Char(string="Final")
    cost = fields.Char(string="Costo")
    total = fields.Char(string="Total") """
