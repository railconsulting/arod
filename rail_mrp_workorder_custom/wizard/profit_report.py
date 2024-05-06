# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError
from collections import defaultdict
import xlsxwriter, io, base64, logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class SaleProfitReport(models.TransientModel):
    _name = 'sale.profit.report'
    _description = "Profit report"

    xls_file = fields.Binary(string="Data")
    name = fields.Char(string='File Name', readonly=True)
    date_from = fields.Date("Desde", required=True)
    date_to = fields.Date("Hasta", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    currency_ids = fields.Many2many('res.currency', string="Divisa")
    branch_ids = fields.Many2many('res.branch', string="Sucursal")
    categ_ids = fields.Many2many('product.category', string="Categoria")
    product_ids = fields.Many2many('product.product', string="Productos")
    partner_tags = fields.Many2many('res.partner.category', string="Categoria cliente")
    user_ids = fields.Many2many('res.users', string="Vendedores")

    def get_report_data(self):
        domain = [
            ('date','>=',self.date_from),
            ('date','<=',self.date_to),
            ('move_type','=', 'out_invoice',)
        ]
        line_domain = []
        if self.branch_ids:
            domain.append(('move_id.branch_id','in', self.branch_ids.ids))
        if self.currency_ids:
            domain.append(('move_id.currency_id','in', self.currency_id.ids))
        if self.partner_tags:
            domain.append(('move_id.partner_id.category_id','in', self.partner_tags.ids))
        if self.user_ids:
            domain.append(('move_id.invoice_user_id','in', self.user_ids.ids))
        if self.categ_ids:
            domain.append(('product_id.categ_id','in', self.categ_ids.ids))
            line_domain.append(('product_id.categ_id','in', self.categ_ids.ids))
        if self.product_ids:
            domain.append(('product_id','in',self.product_ids.ids))
            line_domain.append(('product_id','in',self.product_ids.ids))


        lines = self.env['account.move.line'].search(domain)
        invoice_domain = []
        for l in lines:
            invoice_domain.append(l.move_id.id)
        invoice_domain = list(set(invoice_domain))
        moves = self.env['account.move'].browse(invoice_domain)
        data = []
        for m in moves:
            source_orders = m.line_ids.sale_line_ids.filtered_domain(line_domain).order_id
            source_stocklayers = source_orders.order_line.move_ids.filtered_domain(line_domain).stock_valuation_layer_ids
            inv_lines = m.line_ids.filtered_domain(line_domain)
            devs = source_orders.order_line.move_ids.filtered(lambda x: x.picking_code == 'incoming')
            devs = devs.filtered_domain(line_domain).stock_valuation_layer_ids
            nc = self.env['account.move'].search([('reversed_entry_id','=',m.id)])
            nc_lines = nc.line_ids.filtered_domain(line_domain)
            if m.l10n_mx_edi_cfdi_uuid:
                folio = m.l10n_mx_edi_cfdi_uuid.rsplit("-",1)[-1]
            else:
                folio = m.name
            #amount variables
            free_delivery = sum(o.shipping_total for o in source_orders.filtered(lambda x: x.shipping_type == x.shipping_type == 'free'))
            customer_delivery = sum(o.shipping_total for o in source_orders.filtered(lambda x: x.shipping_type == x.shipping_type == 'customer'))
            invoice_cost = sum(abs(p.value) for p in source_stocklayers)
            invoice_total = sum(l.credit for l in inv_lines)
            invoice_perc = 0.00 #TODO Consultar como se calcula correctamente

            nc_cost = sum(abs(d.value) for d in devs)
            nc_total = sum(l.credit for l in nc_lines)
            nc_porc = 0.00 #TODO Consultar como se calcula correctamente

            bonus_total = 0.00 #TODO Consultar como se calcula correctamente
            bonus_perc = 0.00 #TODO Consultar como se calcula correctamente

            ctrl1 = sum(l.quantity for l in inv_lines)
            ctrl2 = sum(l.quantity for l in nc_lines)

            #NOTE Creo que estos se deben calcular restando los valores de facturas - devoluciones y notas de credito
            subtotal = sum(l.credit for l in inv_lines)
            tax = sum(l.price_total - l.price_subtotal for l in inv_lines)
            net = sum(l.price_total for l in inv_lines)
            cost_subtotal = sum(abs(p.value) for p in source_stocklayers)
            profit = subtotal - cost_subtotal
            profit_perc = 0.00

            vals={
                'folio': m.branch_id.code if m.branch_id.code else '' + "-" + folio,
                'comentario': ', '.join(o.name for o in source_orders),
                'fecha': m.date.strftime("%d/%m/%Y"),
                'cliente': m.partner_id.display_name,
                'factura': m.name,
                'envio_gratis': free_delivery,
                'envio_cliente': customer_delivery,
                'costo': invoice_cost,
                'invoice_total': invoice_total,
                'invoice_porc': invoice_perc, 
                'costo_dev': nc_cost,
                'nc_total': nc_total,
                'nc_porc': nc_porc,
                'bonif_total': bonus_total, 
                'bonif_porc': bonus_perc,
                'ctrl1': ctrl1,
                'ctrl2': ctrl2,
                'subtotal': subtotal,
                'impuesto': tax,
                'neto': net,
                'subtotal_costo': cost_subtotal,
                'utilidad_bruta': profit, 
                'utilidad_porc': profit_perc,
            }

            data.append(vals)              
        return data
    
    def build_xlsx(self):
        date_from = self.date_from
        date_to = self.date_to
        company = self.company_id
        f = io.BytesIO()
        xls_filename = "Tabla de gastos " + company.name+ "_" +str(date_from.strftime('%d/%m/%Y')) + "_" + str(date_to.strftime('%d/%m/%Y'))
        book = xlsxwriter.Workbook(f)
        sheet = book.add_worksheet('Gastos')
        company_name = company.name.upper()
        print_dt = datetime.now()

        #row_styles
        main_header = book.add_format({
            'bold':True,
            'font_color': 'black',
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Calibri',
            'font_size': 18,
        })
        table_header = book.add_format({
            'border': 1,
            'bold':True,
            'font_color': 'white',
            'bg_color': '#01263A',
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
        })
        table_footer = book.add_format({
            'border': 1,
            'bold':True,
            'bg_color': '#CC9D2E',
            'font_color': 'black',
            'align': 'right',
            'valign': 'vcenter',
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
            'num_format': '[$'+company.currency_id.symbol+']#,##0.00',
        })
        calibri_12 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 11,
            'align': 'left',
            'text_wrap': True,
            'num_format': 2,
            'bold': True,
        })
        calibri_11 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 11,
            'text_wrap': True,
            'num_format': 2,
            'font_color':'#31869B',
        })
        calibri_10 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'align': 'right',
            'num_format': '[$'+company.currency_id.symbol+']#,##0.00',
        })
        calibri_9 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 9,
            'num_format': 2,
            'align': 'center',
            'bold': True,
        })

        sheet.merge_range(0, 0, 0, 3, company_name, main_header)
        sheet.merge_range(1, 0, 1, 3, 'REPORTE DE RENTABILIDAD', calibri_12)
        sheet.write(2, 0, 'FECHA INICIAL:')
        sheet.write(2, 1, date_from.strftime('%d/%m/%Y'), calibri_11 )
        sheet.write(3, 0, 'FECHA FINAL:')
        sheet.write(3, 1, date_to.strftime('%d/%m/%Y'), calibri_11 )

        row = 6
        sheet.merge_range(row, 0, row +1, 0, "FOLIO", table_header)
        sheet.merge_range(row, 1, row +1, 1, "COMENTARIO", table_header)
        sheet.merge_range(row, 2, row +1, 2, "FECHA", table_header)
        sheet.merge_range(row, 3, row +1, 3, "CLIENTE", table_header)
        sheet.merge_range(row, 4, row +1, 4, "FACTURA / REFERENCIA", table_header)
        sheet.merge_range(row, 5, row +1, 5, "COSTO ENVIO GRATIS", table_header)
        sheet.merge_range(row, 6, row +1, 6, "COSTO ENVIO CLIENTE", table_header)
        sheet.merge_range(row, 7, row +1, 7, "COSTO", table_header)
        sheet.merge_range(row, 8, row +1, 8, "SUB-TOTAL", table_header)
        sheet.merge_range(row, 9, row +1, 9, "%", table_header)
        sheet.merge_range(row, 10, row, 12, "DEVOLUCIONES", table_header)
        sheet.write(row +1, 10, "COSTO", table_header)
        sheet.write(row +1, 11, "SUB-TOTAL", table_header)
        sheet.write(row +1, 12, "%", table_header)
        sheet.merge_range(row, 13, row, 14, "BONIFICACIONES", table_header)
        sheet.write(row +1, 13, "SUB-TOTAL", table_header)
        sheet.write(row +1, 14, "%", table_header)
        sheet.merge_range(row, 15, row, 22, "TOTAL", table_header)
        sheet.write(row +1, 15, "CTRL-1", table_header)
        sheet.write(row +1, 16, "CTRL-2", table_header)
        sheet.write(row +1, 17, "SUB-TOTAL", table_header)
        sheet.write(row +1, 18, "IMPUESTO", table_header)
        sheet.write(row +1, 19, "NETO", table_header)
        sheet.write(row +1, 20, "COSTO", table_header)
        sheet.write(row +1, 21, "U. BRUTA", table_header)
        sheet.write(row +1, 22, "%", table_header)

        data = self.get_report_data()
        row += 2
        tot5=tot6=tot7=tot8=tot9=tot10=tot11=tot12=tot13 = 0
        tot14=tot15=tot16=tot17=tot18=tot19=tot20=tot21=tot22 =0
        for d in data:
            sheet.write(row, 0, d['folio'], calibri_10)
            sheet.write(row, 1, d['comentario'], calibri_10)
            sheet.write(row, 2, d['fecha'], calibri_10)
            sheet.write(row, 3, d['cliente'], calibri_10)
            sheet.write(row, 4, d['factura'], calibri_10)
            sheet.write(row, 5, d['envio_gratis'], calibri_10)
            sheet.write(row, 6, d['envio_cliente'], calibri_10)
            sheet.write(row, 7, d['costo'], calibri_10)
            sheet.write(row, 8, d['invoice_total'], calibri_10)
            sheet.write(row, 9, d['invoice_porc'], calibri_10)
            sheet.write(row, 10, d['costo_dev'], calibri_10)
            sheet.write(row, 11, d['nc_total'], calibri_10)
            sheet.write(row, 12, d['nc_porc'], calibri_10)
            sheet.write(row, 13, d['bonif_total'], calibri_10)
            sheet.write(row, 14, d['bonif_porc'], calibri_10)
            sheet.write(row, 15, d['ctrl1'], calibri_10)
            sheet.write(row, 16, d['ctrl2'], calibri_10)
            sheet.write(row, 17, d['subtotal'], calibri_10)
            sheet.write(row, 18, d['impuesto'], calibri_10)
            sheet.write(row, 19, d['neto'], calibri_10)
            sheet.write(row, 20, d['subtotal_costo'], calibri_10)
            sheet.write(row, 21, d['utilidad_bruta'], calibri_10)
            sheet.write(row, 22, d['utilidad_porc'], calibri_10)
            tot5 += d['envio_gratis']
            tot6 += d['envio_cliente']
            tot7 += d['costo']
            tot8 += d['invoice_total']
            tot9 += d['invoice_porc']
            tot10 += d['costo_dev']
            tot11 += d['nc_total']
            tot12 += d['nc_porc']
            tot13 += d['bonif_total']
            tot14 += d['bonif_porc']
            tot15 += d['ctrl1']
            tot16 += d['ctrl2']
            tot17 += d['subtotal']
            tot18 += d['impuesto']
            tot19 += d['neto']
            tot20 += d['subtotal_costo']
            tot21 += d['utilidad_bruta']
            tot22 += d['utilidad_porc']

            row += 1

        sheet.merge_range(row, 0, row, 4, "TOTAL REGISTROS: " + str(len(data)), table_footer)
        sheet.write(row, 5, tot5, table_footer)
        sheet.write(row, 6, tot6, table_footer)
        sheet.write(row, 7, tot7, table_footer)
        sheet.write(row, 8, tot8, table_footer)
        sheet.write(row, 9, tot9, table_footer)
        sheet.write(row, 10, tot10, table_footer)
        sheet.write(row, 11, tot11, table_footer)
        sheet.write(row, 12, tot12, table_footer)
        sheet.write(row, 13, tot13, table_footer)
        sheet.write(row, 14, tot14, table_footer)
        sheet.write(row, 15, tot15, table_footer)
        sheet.write(row, 16, tot16, table_footer)
        sheet.write(row, 17, tot16, table_footer)
        sheet.write(row, 18, tot18, table_footer)
        sheet.write(row, 19, tot19, table_footer)
        sheet.write(row, 20, tot20, table_footer)
        sheet.write(row, 21, tot21, table_footer)
        sheet.write(row, 22, tot22, table_footer)

        sheet.set_column(0,0,20)
        sheet.set_column(1,1,25)
        sheet.set_column(2,2,12)
        sheet.set_column(3,3,50)
        sheet.set_column(4,4,25)
        sheet.set_column(5,22,15)



        book.close()
        self.xls_file = base64.encodebytes(f.getvalue())
        self.name = xls_filename + ".xlsx"
        """ self.write({
            'xls_file': base64.encodebytes(f.getvalue()),
            'name': xls_filename + ".xlsx"
        }) """

    def download_xls(self):
        self.build_xlsx()
        return {
            'name': 'Reporte de rentabilidad',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }


