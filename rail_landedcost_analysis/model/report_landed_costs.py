from odoo import fields, models, api
from odoo.exceptions import UserError,ValidationError
import xlsxwriter, io, base64

class ReportLandedCosts(models.Model):
    _inherit = 'stock.landed.cost'

    _description = "Landed Costs Report"
    xls_file = fields.Binary(string='Download',filename='name')
    xls_name = fields.Char(string='File name', size=64)

    def get_prepared_data(self):
        if self.valuation_adjustment_lines:
            header = set([line.cost_line_id.name if line.cost_line_id else 'False'  for line in self.valuation_adjustment_lines])
            product_list = set([line.product_id.name for line in self.valuation_adjustment_lines])
            product_datas = {product : {} for product in product_list}
            datas = dict()
            for line in self.valuation_adjustment_lines:
                if line.product_id.name not in datas.keys():
                    datas.update({
                        line.product_id.name:
                        {
                            'product_code': line.product_id.default_code,
                            'original_value' : line.former_cost,
                            'qty' : line.quantity,
                            'final_cost': line.final_cost,
                            'data' : {line.cost_line_id.name if line.cost_line_id else 'False' : line.additional_landed_cost}
                        }
                    })
                else:
                    datas[line.product_id.name]['data'].update({
                        line.cost_line_id.name if line.cost_line_id else 'False' : line.additional_landed_cost
                        })
            head_dict = {}
            for head in header:
                total = 0
                for data in datas:
                    total += datas[data]['data'].get(head, 0)
                head_dict.update({
                    head:total,
                    })
                total = 0
            total_final_cost, total_original_value, total_qty = 0, 0, 0
            for data in datas:
                total_qty += datas[data]['qty']
                total_original_value += datas[data]['original_value']
                total_final_cost += datas[data]['final_cost']
            head_dict.update({
                'total_final_cost' : total_final_cost,
                'total_original_value' : total_original_value,
                'total_qty' : total_qty
                    })
            return [header, datas, head_dict]
        else:
            raise ValidationError("Primero debe de dar click en el boton de calcular")

    def xlsx_report(self):
        f = io.BytesIO()
        xls_filename = 'Analisis_prorrateo.xlsx'
        workbook = xlsxwriter.Workbook(f)
        sheet = workbook.add_worksheet('Prorrateo')
        row, col = 8, 0
        values = self.get_prepared_data()
        sheet.set_page_view()
        sheet.set_paper(3)
        sheet.set_landscape()
        sheet.hide_gridlines(2)
        #sheet.set_print_scale(39)
        sheet.fit_to_pages(1,0)
        #sheet.set_start_page(self.folio)
        company_id = self.env.user.company_id
        if company_id.partner_id.image_128:
            company_logo = io.BytesIO(base64.b64decode(company_id.partner_id.image_128))
        else:
            company_logo = io.BytesIO(base64.b64decode(company_id.partner_id.avatar_128))
        xls_date = self.date.strftime('%d/%m/%Y')
        report_title = "Analisis prorrateo" + '\n' + xls_date + '\n' + self.name
        company_data = company_id.partner_id.contact_address
        header_text = '&R&12&"Calibri,Bold"{}'.format(report_title)+'&C&9&"Calibri,Bold"{}&L&G'.format(company_data)                    
        sheet.set_header(header_text,{'image_left': 'logo.png', 'image_data_left': company_logo, 'x_scale': 0.6, 'y_scale': 0.8})
        #self.sheet.set_h_pagebreaks([64])
        sheet.set_column(0, 10, 15)

        main_header = workbook.add_format({
            'bold':True,
            'border': 1,
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
        })
        sub_header = workbook.add_format({
            'bold':True,
            'align': 'center',
            'valign': 'vcenter',
        })
        subtotal_text = workbook.add_format({
            'bold': True,
            'italic': True,
            'bottom': 6,
        })
        subtotal_money = workbook.add_format({
            'bold': True,
            'italic': True,
            'bottom': 6,
            'num_format': '[$'+company_id.currency_id.symbol+']#,##0.00',
        })
        subtotal_expenses = workbook.add_format({
            'bold': True,
            'num_format': '[$'+company_id.currency_id.symbol+']#,##0.00',
        })
        expense_header = workbook.add_format({
            'bold':True,
            'border': 1,
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E3DFED',
        })        
        money_style = workbook.add_format({
            'num_format': '[$'+company_id.currency_id.symbol+']#,##0.00',
        })


        '''Header'''
        sheet.write(4, 0, 'Codigo', main_header)
        sheet.write(4, 1, 'Producto', main_header)
        sheet.write(4, 2, 'Cantidad', main_header)
        sheet.write(4, 3, 'Costo U. origen', main_header)
        sheet.write(4, 4, 'Total origen', main_header)
        headingcol = 5
        for val in values[0]:
            sheet.write(4, headingcol, val, expense_header)
            headingcol += 1
        sheet.write(4, headingcol, 'Total gastos', main_header)
        sheet.write(4, headingcol+1, 'Valor prorrateado', main_header)
        sheet.write(4, headingcol+2, 'Costo U. prorrateo', main_header)

        row = 6
        
        total_origen = 0
        total_new_cost = 0
        '''Data'''
        for data in values[1]:
            sheet.write(row, 0, values[1][data]['product_code'])
            sheet.write(row, 1, data)
            sheet.write(row, 2, values[1][data]['qty'])
            #Unit FOB
            sheet.write(row, 3, values[1][data]['original_value'] / values[1][data]['qty'], money_style)
            #Total FOB
            sheet.write(row, 4, values[1][data]['original_value'], money_style)
            total_additional_landed_cost = 0
            col = 5
            for val in values[0]:
                if values[1][data]['data'].get(val):
                    sheet.write(row, col, values[1][data]['data'][val], money_style)
                    total_additional_landed_cost += values[1][data]['data'][val]
                else:
                    sheet.write(row, col, 0, money_style)
                col += 1
            sheet.write(row, col, total_additional_landed_cost, subtotal_expenses)

            total_origen += values[1][data]['original_value'] / values[1][data]['qty']

            #Total with expenses
            sheet.write(row, col+1, values[1][data]['original_value'] + total_additional_landed_cost, money_style)
            #Unit cost with expenses
            sheet.write(row, col+2, (values[1][data]['original_value'] + total_additional_landed_cost) / values[1][data]['qty'])
            total_new_cost += (values[1][data]['original_value'] + total_additional_landed_cost) / values[1][data]['qty']
            row += 1
            col = 0

        '''Total data'''
        total_head_additional_landed_cost = 0
        row +=1
        sheet.write(row, 2, values[2]['total_qty'], subtotal_text)
        sheet.write(row, 3, total_origen, subtotal_money)
        sheet.write(row, 4, values[2]['total_original_value'], subtotal_money)
        totalheadingcol = 5
        for value in values[0]:
            sheet.write(row, totalheadingcol, values[2][value], subtotal_money)
            total_head_additional_landed_cost += values[2][value]
            totalheadingcol += 1
        sheet.write(row, totalheadingcol, total_head_additional_landed_cost, subtotal_money)
        sheet.write(row, totalheadingcol+1, values[2]['total_original_value'] + total_head_additional_landed_cost, subtotal_money)
        sheet.write(row, totalheadingcol+2, total_new_cost, subtotal_money)

        workbook.close()
        self.write({
            'xls_file': base64.encodebytes(f.getvalue()),
            'xls_name': 'Analisis_prorrateo.xlsx'
        })

    def xls_export_dwn(self):
        self.xlsx_report()
        return {
            'name': 'Analisis prorrateo',
            'type': 'ir.actions.act_url',
            'url': "/web/content/?model=stock.landed.cost&id=" + str(self.id) + "&field=xls_file&download=true&filename=Analisis_prorrateo.xlsx",
            'target': 'self',
        }
