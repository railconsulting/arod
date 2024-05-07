# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError
from collections import defaultdict
import xlsxwriter, io, base64, logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class BankFlowWizard(models.TransientModel):
    _name = 'bank.flow.wizard'
    _description = "Bank Flow"

    xls_file = fields.Binary(string="Data")
    name = fields.Char(string='File Name', readonly=True)
    date_from = fields.Date("Desde", required=True)
    date_to = fields.Date("Hasta", required=True)
    journal_ids = fields.Many2many('account.journal', domain=[('type','=','bank')])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)

    def get_report_data(self):
        move_lines = self.env['account.move.line']
        domain = [('parent_state','=','posted'),('date','>=', self.date_from),('date','<=',self.date_to)]
        journal_domain = [('type','=','bank')]
        if self.journal_ids:
            domain.append(('journal_id','in', self.journal_ids.ids))
            journal_domain.append(('id','in', self.journal_ids.ids))
        journals = self.env['account.journal'].search(journal_domain)
        moves = move_lines.search(domain)
        report_dict = defaultdict(lambda: {'initial': 0.00, 'ending': 0.00, 'income_moves': [], 'outcome_moves': []})
        final_dict = {}
        for j in journals:
            initial_lines = move_lines.search([('account_id','=', j.default_account_id.id),('date','<=', self.date_from),('account_id','=', j.default_account_id.id)])
            initial_balance = sum(line.debit for line in initial_lines) - sum(line.credit for line in initial_lines)
            ending_balance = sum(line.debit for line in moves.filtered(lambda x: x.account_id.id == j.default_account_id.id)) \
                            - sum(line.credit for line in moves.filtered(lambda x: x.account_id.id == j.default_account_id.id))
            report_dict[j.name]['initial'] = initial_balance
            report_dict[j.name]['ending'] = ending_balance
            for m in moves.filtered(lambda x: x.account_id.id == j.default_account_id.id):
                
                if m.debit > 0:
                    report_dict[m.journal_id.name]['income_moves'].append({
                        'name': m.move_id.name,
                        'ref': m.move_id.ref,
                        'amount': m.debit,
                    })
                else:
                    report_dict[m.journal_id.name]['outcome_moves'].append({
                        'name': m.move_id.name,
                        'ref': m.move_id.ref,
                        'amount': m.credit,
                    })
            final_dict[j.name] = report_dict[j.name]
            

        #raise ValidationError(str(final_dict))
        return final_dict
    
    def build_xlsx(self):
        date_from = self.date_from
        date_to = self.date_to
        company = self.company_id
        f = io.BytesIO()
        xls_filename = "Flujo bancario " + company.name +str(date_from.strftime('%d/%m/%Y')) + "_" + str(date_to.strftime('%d/%m/%Y'))
        book = xlsxwriter.Workbook(f)
        sheet = book.add_worksheet('Flujo')
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
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
        })
        table_footer = book.add_format({
            'border': 1,
            'bold':True,
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
            'num_format': 2,
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
            'num_format': 2,
        })
        calibri_9 = book.add_format({
            'font_name': 'Calibri',
            'font_size': 9,
            'num_format': 2,
            'align': 'center',
            'bold': True,
        })

        sheet.merge_range(0, 0, 0, 3, company_name, main_header)
        sheet.merge_range(1, 0, 1, 3, 'FLUJO DE EFECTIVO DETALLADO', calibri_12)
        sheet.write(2, 0, 'FECHA INICIAL:')
        sheet.write(2, 1, date_from.strftime('%d/%m/%Y'), calibri_11 )
        sheet.write(3, 0, 'FECHA FINAL:')
        sheet.write(3, 1, date_to.strftime('%d/%m/%Y'), calibri_11 )

        sheet.write(6, 0, 'BANCO', table_header)
        sheet.write(6, 1, 'SALDO INICIAL', table_header)
        sheet.merge_range(6, 2, 6, 4, 'INGRESOS', table_header)
        sheet.merge_range(6, 5, 6, 7, 'EGRESOS', table_header)
        sheet.write(6, 8, 'FLUJO', table_header)
        sheet.write(6, 9, 'SALDO FINAL', table_header)
        sheet.write(6, 10, 'DIFERENCIA', table_header)
        sheet.write(7, 1, "MONTO", calibri_9)
        sheet.write(7, 2, "#", calibri_9)
        sheet.write(7, 3, "REF", calibri_9)
        sheet.write(7, 4, "MONTO", calibri_9)
        sheet.write(7, 5, "#", calibri_9)
        sheet.write(7, 6, "REF", calibri_9)
        sheet.write(7, 7, "MONTO", calibri_9)
        report_data = self.get_report_data()
        row = 8
        for journal, data in report_data.items():
            initial = data['initial']
            ending = data['ending']
            sheet.write(row, 0, journal, calibri_11)
            sheet.write(row, 1, initial, calibri_11)
            in_moves = data['income_moves']
            out_moves = data['outcome_moves']
            total_in = sum(im['amount'] for im in in_moves)
            total_out = sum(om['amount'] for om in out_moves)
            sheet.write(row, 4, total_in, calibri_11)
            sheet.write(row, 7, total_out, calibri_11)
            sheet.write(row, 8, total_in - total_out, calibri_11)
            sheet.write(row, 9, initial - (total_in - total_out), calibri_11)
            sheet.write(row, 10, ending, calibri_11)
            in_rows = len(in_moves)
            row += 1
            if in_moves:
                for income in in_moves:
                    sheet.write(row, 2, income['name'], calibri_10)
                    sheet.write(row, 3, income['ref'] if income['ref'] else '', calibri_10)
                    sheet.write(row, 4, income['amount'], calibri_10)
                    row += 1
            out_rows = len(out_moves)
            if out_moves:
                row -= in_rows
                for outcome in out_moves:
                    sheet.write(row, 5, outcome['name'], calibri_10)
                    sheet.write(row, 6, outcome['ref']if outcome['ref'] else '', calibri_10)
                    sheet.write(row, 7, outcome['amount'], calibri_10)
                    row += 1
            else:
                row += 1
            row += (in_rows - out_rows)
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 25)
        sheet.set_column(7, 10, 15)
        book.close()
        self.update({
            'xls_file': base64.encodebytes(f.getvalue()),
            'name': xls_filename + ".xlsx"
        })




    def download_xls(self):
        self.build_xlsx()
        return {
            'name': 'Reporte flujo de bancos',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }





