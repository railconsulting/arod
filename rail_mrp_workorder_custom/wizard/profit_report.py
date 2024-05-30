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
    dev_factor = fields.Float("Factor", default=5)

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
            domain.append(('move_id.currency_id','in', self.currency_ids.ids))
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
            factor = self.dev_factor
            source_orders = m.line_ids.sale_line_ids.filtered_domain(line_domain).order_id
            source_stocklayers = source_orders.order_line.move_ids.filtered_domain(line_domain).stock_valuation_layer_ids
            inv_lines = m.line_ids.filtered_domain(line_domain)
            devs = source_orders.order_line.move_ids.filtered(lambda x: x.picking_code == 'incoming')
            devs = devs.filtered_domain(line_domain).stock_valuation_layer_ids
            nc = self.env['account.move'].search([('reversed_entry_id','=',m.id)])
            nc_lines_dev = nc.line_ids.filtered_domain(line_domain).filtered(lambda x: x.product_id.detailed_type == 'product')
            nc_lines_bon = nc.line_ids.filtered_domain(line_domain).filtered(lambda x: x.product_id.detailed_type == 'service')
            if m.l10n_mx_edi_cfdi_uuid:
                folio = m.l10n_mx_edi_cfdi_uuid.rsplit("-",1)[-1]
            else:
                folio = m.name
            #amount variables

            #invoice
            invoice_cost = sum(abs(p.value) for p in source_stocklayers)
            invoice_subtotal = sum(l.credit for l in inv_lines)
            invoice_tax = sum(l.price_total - l.price_subtotal for l in inv_lines)
            invoice_perc = ((invoice_subtotal - invoice_cost) / invoice_subtotal) * 100

            #devs
            cv = invoice_cost / sum(l.quantity for l in inv_lines)
            pv = invoice_subtotal / sum(l.quantity for l in inv_lines)
            nc_cost = cv * factor
            nc_subtotal = pv * factor
            nc_net_cost = invoice_cost - nc_cost
            nc_tax = sum(l.price_total - l.price_subtotal for l in nc_lines_dev)
            nc_net_subtotal = invoice_subtotal - nc_subtotal
            nc_porc = ((nc_net_subtotal - nc_net_cost) / nc_net_subtotal) * 100

            #bonif
            bonus_subtotal =  sum(abs(l.debit) for l in nc_lines_bon)
            bonus_cost = nc_net_cost
            bonus_net_subtotal = nc_net_subtotal - bonus_subtotal
            bonus_tax = sum(l.price_total - l.price_subtotal for l in nc_lines_bon)
            bonus_perc = ((bonus_net_subtotal - bonus_cost) / bonus_net_subtotal) * 100

            #total
            ctrl1 = sum(l.quantity for l in inv_lines)
            ctrl2 = sum(l.quantity for l in nc_lines_dev)
            subtotal = invoice_subtotal - (nc_subtotal + bonus_subtotal)
            tax = invoice_tax - (nc_tax + bonus_tax)
            net = subtotal + tax
            cost_subtotal = nc_net_cost
            profit = subtotal - cost_subtotal
            profit_perc = ((subtotal - cost_subtotal) / subtotal) * 100

            #delivery
            free_delivery = sum(o.shipping_total for o in source_orders.filtered(lambda x: x.shipping_type == x.shipping_type == 'free'))
            customer_delivery = sum(o.shipping_total for o in source_orders.filtered(lambda x: x.shipping_type == x.shipping_type == 'customer'))
            if bonus_cost > 0 and free_delivery > 0 and customer_delivery > 0:
                delivery_perc = ((bonus_cost / ((free_delivery + customer_delivery) - bonus_cost)) / bonus_cost) * 100
            else:
                delivery_perc = 0

            vals={
                '0': m.branch_id.code if m.branch_id.code else '' + "-" + folio,
                '1': ', '.join(o.name for o in source_orders),
                '2': m.date.strftime("%d/%m/%Y"),
                '3': m.partner_id.display_name,
                '4': m.name,
                '5': invoice_cost,
                '6': invoice_subtotal,
                '7': invoice_perc, 
                '8': nc_cost,
                '9': nc_subtotal,
                '10': nc_net_cost,
                '11': nc_net_subtotal,
                '12': nc_porc,
                '13': bonus_subtotal, 
                '14': bonus_cost,
                '15': bonus_net_subtotal,
                '16': bonus_perc,
                '17': ctrl1,
                '18': ctrl2,
                '19': subtotal,
                '20': tax,
                '21': net,
                '22': cost_subtotal,
                '23': profit,
                '24': profit_perc,
                '25': free_delivery + customer_delivery,
                '26': (free_delivery + customer_delivery) - bonus_cost,
                '27': bonus_cost,
                '28': delivery_perc,
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
        sheet.merge_range(row, 0, row, 7, "DOCUMENTO", table_header)
        sheet.write(row +1, 0, "FOLIO", table_header)
        sheet.write(row +1, 1, "COMENTARIO", table_header)
        sheet.write(row +1, 2, "FECHA", table_header)
        sheet.write(row +1, 3, "CLIENTE", table_header)
        sheet.write(row +1, 4, "FACTURA / REFERENCIA", table_header)
        sheet.write(row +1, 5, "COSTO", table_header)
        sheet.write(row +1, 6, "SUB-TOTAL", table_header)
        sheet.write(row +1, 7, "%", table_header)
        sheet.merge_range(row, 8, row, 10, "DEVOLUCIONES", table_header)
        sheet.write(row +1, 8, "COSTO", table_header)
        sheet.write(row +1, 9, "SUB-TOTAL", table_header)
        sheet.write(row +1, 10, "COSTO NETO", table_header)
        sheet.write(row +1, 11, "SUB-NETO", table_header)
        sheet.write(row +1, 12, "%", table_header)
        sheet.merge_range(row, 13, row, 16, "BONIFICACIONES", table_header)
        sheet.write(row +1, 13, "SUB-TOTAL", table_header)
        sheet.write(row +1, 14, "COSTO", table_header)
        sheet.write(row +1, 15, "SUBTOTAL", table_header)
        sheet.write(row +1, 16, "%", table_header)
        sheet.merge_range(row, 17, row, 24, "TOTAL", table_header)
        sheet.write(row +1, 17, "CTRL-1", table_header)
        sheet.write(row +1, 18, "CTRL-2", table_header)
        sheet.write(row +1, 19, "SUB-TOTAL", table_header)
        sheet.write(row +1, 20, "IMPUESTO", table_header)
        sheet.write(row +1, 21, "NETO", table_header)
        sheet.write(row +1, 22, "COSTO", table_header)
        sheet.write(row +1, 23, "U. BRUTA", table_header)
        sheet.write(row +1, 24, "%", table_header)
        sheet.merge_range(row, 25, row, 28, "FLETES", table_header)
        sheet.write(row +1, 25, "FLETE", table_header)
        sheet.write(row +1, 26, "COSTO CTRL", table_header)
        sheet.write(row +1, 27, "SUB-TOTAL", table_header)
        sheet.write(row +1, 28, "%", table_header)

        data = self.get_report_data()
        row += 2
        tot5=tot6=tot7=tot8=tot9=tot10=tot11=tot12=tot13 = 0
        tot14=tot15=tot16=tot17=tot18=tot19=tot20=tot21=tot22=tot23=tot24 =0
        for d in data:
            sheet.write(row, 0, d['0'], calibri_10)
            sheet.write(row, 1, d['1'], calibri_10)
            sheet.write(row, 2, d['2'], calibri_10)
            sheet.write(row, 3, d['3'], calibri_10)
            sheet.write(row, 4, d['4'], calibri_10)
            sheet.write(row, 5, d['5'], calibri_10)
            sheet.write(row, 6, d['6'], calibri_10)
            sheet.write(row, 7, d['7'], calibri_10)
            sheet.write(row, 8, d['8'], calibri_10)
            sheet.write(row, 9, d['9'], calibri_10)
            sheet.write(row, 10, d['10'], calibri_10)
            sheet.write(row, 11, d['11'], calibri_10)
            sheet.write(row, 12, d['12'], calibri_10)
            sheet.write(row, 13, d['13'], calibri_10)
            sheet.write(row, 14, d['14'], calibri_10)
            sheet.write(row, 15, d['15'], calibri_10)
            sheet.write(row, 16, d['16'], calibri_10)
            sheet.write(row, 17, d['17'], calibri_10)
            sheet.write(row, 18, d['18'], calibri_10)
            sheet.write(row, 19, d['19'], calibri_10)
            sheet.write(row, 20, d['20'], calibri_10)
            sheet.write(row, 21, d['21'], calibri_10)
            sheet.write(row, 22, d['22'] , calibri_10)
            sheet.write(row, 23, d['23'], calibri_10)
            sheet.write(row, 24, d['24'], calibri_10)
            sheet.write(row, 25, d['25'], calibri_10)
            sheet.write(row, 26, d['26'], calibri_10)
            sheet.write(row, 27, d['27'], calibri_10)
            sheet.write(row, 28, d['28'], calibri_10)
            tot5 += d['5']
            tot6 += d['6']
            tot7 += d['7']
            tot8 += d['8']
            tot9 += d['9']
            tot10 += d['10']
            tot11 += d['11']
            tot12 += d['12']
            tot13 += d['13']
            tot14 += d['14']
            tot15 += d['15']
            tot16 += d['16']
            tot17 += d['17']
            tot18 += d['18']
            tot19 += d['19']
            tot20 += d['20']
            tot21 += d['21']
            tot22 += d['22']
            tot23 += d['23']
            tot24 += d['24']

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
        sheet.write(row, 23, tot23, table_footer)


        sheet.set_column(0,0,20)
        sheet.set_column(1,1,25)
        sheet.set_column(2,2,12)
        sheet.set_column(3,3,50)
        sheet.set_column(4,4,25)
        sheet.set_column(5,24,15)



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


