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
        table_header = book.add_format({
            'border': 1,
            'bold':True,
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Calibri',
            'font_size': 11,
            #'text_wrap': True,
        })
        calibri_12 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
            'num_format': 2,
        })
        calibri_12_bold = book.add_format({
            'bold': True,
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
            'num_format': 2,
        })
        calibri_12_blue = book.add_format({
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
            'num_format': 2,
            'font_color': 'blue'
        })
        calibri_10 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'text_wrap': True,
            'num_format': 2,
        })
        calibri_9 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 9,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
        })

        data = {}
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        locations = self.get_location()
        data['location_ids'] = locations
        
        sheet.write(0, 0, "KARDEX", main_header)
        sheet.write(0, 1, company.display_name, main_header)
        sheet.write(1, 0, "Condicion:", calibri_12)

        str_condition = "Almacenes: "
        warehouse_list = []
        for w in self.warehouse_ids:
            warehouse_list.append(w.display_name)
        wh = ', '.join(warehouse_list)
        str_condition += wh
        str_condition += "Ubicaciones: "
        location_list = []
        for l in self.location_ids:
            location_list.append(l.display_name)
        loc = ','.join(location_list)
        str_condition += loc

        str_condition += " |    Desde: " + datetime.datetime.strftime(self.date_from,'%d/%m/%Y %H:%M:%S')
        str_condition += " Hasta: " + datetime.datetime.strftime(self.date_to,'%d/%m/%Y %H:%M:%S')

        sheet.merge_range(1, 1, 2, 12, str_condition, calibri_9)
        row = 3
        if self.product_ids:
            products = self.product_ids
        else:
            products = self.env['product.product'].search([])

        for p in products:
            result = self.env['report.kardex.reporte_kardex'].get_lines(data, p.id)

            sheet.write(row, 0, 'PRODUCTO:', calibri_12_blue)
            sheet.merge_range(row, 1, row, 12, p.display_name, calibri_12_blue)
            sheet.write(row, 2, p.barcode if p.barcode else '', calibri_12_bold)
            row += 1
            sheet.write(row, 0, 'Inicial:', calibri_12)
            sheet.write(row, 1, result['totals']['init'], calibri_12_bold)
            sheet.write(row, 2, 'Entradas:', calibri_12)
            sheet.write(row, 3, result['totals']['in'], calibri_12_bold)
            sheet.write(row, 4, 'Salidas:', calibri_12)
            sheet.write(row, 5, result['totals']['out'], calibri_12_bold)
            sheet.write(row, 6, 'Final:', calibri_12)            
            sheet.write(row, 7, result['totals']['init']+result['totals']['in']+result['totals']['out'], calibri_12_bold)

            row += 1
            sheet.write(row, 0, 'Fecha', table_header)
            sheet.write(row, 1, 'Documento', table_header)
            sheet.write(row, 2, '#Venta / #Compra', table_header)
            sheet.write(row, 3, '#Factura', table_header)
            sheet.write(row, 4, 'Empresa', table_header)
            sheet.write(row, 5, 'Tipo', table_header)
            sheet.write(row, 6, 'UOM', table_header)
            sheet.write(row, 7, 'Ubicacion', table_header)
            sheet.write(row, 8, 'Entradas', table_header)
            sheet.write(row, 9, 'Salidas', table_header)
            sheet.write(row, 10, 'Final', table_header)
            sheet.write(row, 11, 'Costo', table_header)
            sheet.write(row, 12, 'Total', table_header)
            row += 1
            for l in result['lines']:
                sheet.write(row, 0, datetime.datetime.strftime(l['date'],'%d/%m/%Y'), calibri_10)
                sheet.write(row, 1, l['document'], calibri_10)
                sheet.write(row, 2, l['order_id'], calibri_10)
                sheet.write(row, 3, l['invoice_id'], calibri_10)
                sheet.write(row, 4, l['company'], calibri_10)
                sheet.write(row, 5, l['type'], calibri_10)
                sheet.write(row, 6, l['uom'], calibri_10)
                sheet.write(row, 7, l['location'], calibri_10)
                sheet.write(row, 8, l['in'], calibri_10)
                sheet.write(row, 9, abs(l['out']), calibri_10)
                sheet.write(row, 10, l['balance'], calibri_10)
                sheet.write(row, 11, l['cost'], calibri_10)
                sheet.write(row, 12, l['balance'] * l['cost'], calibri_10)
                row += 1
            row += 2

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 3, 15)
        sheet.set_column(4, 4, 35)
        sheet.set_column(5, 6, 10)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 12, 10)

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