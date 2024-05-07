# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError
from collections import defaultdict
import xlsxwriter, io, base64, logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class BankFlowWizard(models.TransientModel):
    _name = 'expenses.report.wizard'
    _description = "Expenses report"

    xls_file = fields.Binary(string="Data")
    name = fields.Char(string='File Name', readonly=True)
    date_from = fields.Date("Desde", required=True)
    date_to = fields.Date("Hasta", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    branch_id = fields.Many2one('res.branch')

    def get_report_data(self):
        account_groups = self.env['account.group']
        analytics = self.env['account.analytic.account'].search([])
        main_account_group_id = account_groups.search([('code_prefix_start','=','601')], limit=1)
        groups = account_groups.search([('parent_id','=',main_account_group_id.id)])
        analytic_lines = self.env['account.analytic.line'].search([
            ('general_account_id.group_id','in', groups.ids),
            ('date','>=', self.date_from),
            ('date','<=',self.date_to),
            ('move_line_id.parent_state','=','posted'),
        ])

        report_data = {}
        for group in groups:
            report_data[group.name] = {}
            report_data[group.name]['code'] = group.code_prefix_start
            for analytic in analytics:
                amount = sum(abs(line.amount) for line in analytic_lines.filtered(lambda x: x.general_account_id.group_id.id == group.id and x.account_id.id == analytic.id))
                report_data[group.name][analytic.name] = amount

        return report_data, analytics
    
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
        sheet.merge_range(1, 0, 1, 3, 'TABLA DE GASTOS', calibri_12)
        sheet.write(2, 0, 'FECHA INICIAL:')
        sheet.write(2, 1, date_from.strftime('%d/%m/%Y'), calibri_11 )
        sheet.write(3, 0, 'FECHA FINAL:')
        sheet.write(3, 1, date_to.strftime('%d/%m/%Y'), calibri_11 )

        data = self.get_report_data()
        report_data = data[0]
        analytics = data[1]

        row = 6
        headers = ['CLAVE','TIPO GASTO'] + \
                    [analytic.name for analytic in analytics]
        
        for col, header in enumerate(headers):
            sheet.write(row, col, header, table_header)
        row += 1

        totals = defaultdict(float)

        for group, data in report_data.items():
            sheet.write(row, 0, data['code'], calibri_10)
            sheet.write(row, 1, group, calibri_10)
            col = 2
            for analytic_name, amount in data.items():
                if analytic_name != 'code':
                    sheet.write(row, col, amount, calibri_10)
                    totals[analytic_name] += amount
                    col += 1
            row += 1
        
        sheet.merge_range(row, 0, row, 1, "TOTALES:", table_footer)
        col = 2
        for analytic_name in totals:
            sheet.write(row, col, totals[analytic_name], table_footer)
            col += 1
        row += 1

        sheet.set_column(0,0,10)
        sheet.set_column(1,1,50)
        sheet.set_column(2,100,25)

        book.close()

        self.update({
            'xls_file': base64.encodebytes(f.getvalue()),
            'name': xls_filename + ".xlsx"
        })

    def download_xls(self):
        self.build_xlsx()
        return {
            'name': 'Reporte tabla de gastos',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }