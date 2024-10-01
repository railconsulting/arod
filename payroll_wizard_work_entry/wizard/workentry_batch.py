# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging, xlrd, base64

class WorkEntryWizard(models.TransientModel):
    _name = 'work.entry.wizard'
    _description = 'Batch entries recording'

    payslip_run_id = fields.Many2one('hr.payslip.run', string="Lote")
    work_entry_type_id = fields.Many2one('hr.work.entry.type', string="Tipo entrada")
    work_payslip_ids = fields.One2many('work.entry.wizard.payslips','wizard_id')
    record_type = fields.Selection(string="Tipo actualizacion", selection=[
        ('manual','Manual'),
        ('xls','Excel'),
    ], default='manual')
    method = fields.Selection(string="Metodo de importacion", selection=[
        ('create','Borrar y actualizar'),
        ('update','Leer y actualizar'),
    ], required=True)
    xls_file = fields.Binary(string="Archivo Excel")

    def get_work_payslips(self):
        if self.work_entry_type_id and self.payslip_run_id:
            work_lines_object = self.env['work.entry.wizard.payslips']

            payslips = self.env['hr.payslip'].search([('payslip_run_id','=', self.payslip_run_id.id)])
            worked_days = self.env['hr.payslip.worked_days'].search([
                ('payslip_id','in', payslips.ids),
                ('work_entry_type_id','=', self.work_entry_type_id.id),
            ])
            wizard_lines = []
            for r in payslips:
                vals = {
                    'wizard_id': self.id,
                    'payslip_run_id': self.payslip_run_id.id,
                    'payslip_id': r.id,
                    'work_entry_type_id': self.work_entry_type_id.id,
                    'name': self.work_entry_type_id.name,
                }
                days = 0
                hours = 0
                for wd in worked_days:
                    if wd.payslip_id.id == r.id and self.work_entry_type_id.id == wd.work_entry_type_id.id:
                        days += wd.number_of_days
                        hours += wd.number_of_hours
                        vals.update({
                            'workline_id': wd.id
                        })
                vals.update({
                    'number_of_days': days,
                    'number_of_hours': hours,
                })
                wizard_lines.append(vals) 
            work_lines_object.create(wizard_lines)
        else:
            raise ValidationError(_("Por favor primero elige un tipo de entrada"))
        return {
            'name': 'Registro entradas de trabajo',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,                
        }


    def confirm_work_entries(self):
        if self.work_payslip_ids or self.input_payslip_ids:
            work_entry_object = self.env['hr.payslip.worked_days']
            if self.work_payslip_ids:
                for r in self.work_payslip_ids.filtered(lambda x:x.number_of_days > 0 or x.number_of_hours > 0):
                    if r.workline_id:
                        r.workline_id.update({
                            'number_of_days': r.number_of_days,
                            'number_of_hours': r.number_of_hours,
                        })
                    else:
                        work_entry_object.create({
                            'code': r.work_entry_type_id.code,
                            'contract_id': r.payslip_id.contract_id.id,
                            'name': r.work_entry_type_id.name,
                            'number_of_days': r.number_of_days,
                            'number_of_hours': r.number_of_hours,
                            'payslip_id': r.payslip_id.id,
                            'work_entry_type_id': r.work_entry_type_id.id
                        })
        else:
            raise ValidationError(_("Primero selecciona algun(os) recibo(s)"))
        
    def download_excel_file(self):
        """For downloading a sample excel file"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/download/workentry_excel',
            'target': 'self',
            'file_name': 'import_workentry_template.xlsx'
        }
    
    def import_xls(self):
        if not self.xls_file:
            raise ValidationError("Primero debes elegir una archivo excel a importar.")
        try:
            values = {}
            workbook = xlrd.open_workbook(file_contents=base64.decodebytes(self.xls_file))
            sheet = workbook.sheet_by_index(0)
        except Exception:
                raise ValidationError("El archivo cargado no esta en el formato correcto, por favor revisa tu archivo.\n"\
                                      +"CONSEJO: Da click en guardar como archivo Libro de Excel(*.xlsx)")
        skipped_line_no = []
        ncounter = 2
        wizard_lines = self.env['input.entry.wizard.payslips']
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=', self.payslip_run_id.id)])
        pay_inputs = self.env['hr.payslip.input'].search([
            ('payslip_id','in', payslips.ids),
            ('input_type_id','=', self.input_type_id.id),
        ])
        inputs = self.env['hr.payslip.input.type'].search([])
        employee_obj = self.env['hr.employee']
        lines = []
        for r in range(sheet.nrows):
            #0 empleado
            #1 Codigo/Nombre workentry
            #2 Dias
            #3 Horas
            vals = {
                'wizard_id': self.id
            }
            if sheet.cell(r,0).value not in (None,""):
                employee = sheet.cell(r,0).value
                if not isinstance(employee, str):
                    employee = str(int(employee))
                employee_id = employee_obj.search(['|',('name','=', employee),('barcode','=', employee)])
                if not employee_id:
                    skipped_line_no.append("Fila: "+ str(ncounter -1) + "No se ha encontrado el nombre/codigo del empleado para: " + employee)
                payslip_id = payslips.filtered(lambda x: x.employee_id.name == employee or x.employee_id.barcode == employee)
                if not payslip_id:
                    skipped_line_no.append("Fila: "+ str(ncounter -1) + "No se ha encontrado en recibo para el empleado para: " + employee)
                vals.update({
                    'payslip_run_id': payslip_id.payslip_run_id.id,
                    'payslip_id': payslip_id.id,
                })                  
            else:
                skipped_line_no.append("Fila: "+ str(ncounter -1) + "El valor del nombre/codigo del empleado esta vacio.") 
            if sheet.cell(r,1).value not in (None,""):
                input = sheet.cell(r,1).value
                if not isinstance(input, str):
                    input = str(int(input))
                input_id = inputs.filtered(lambda x: x.name == input or x.code == input)
                if not input_id:
                    skipped_line_no.append("Fila: "+ str(ncounter -1) + "No se ha encontrado una variable para: " + str(input))
                vals.update({
                    'input_type_id': input_id.id,
                })
            else:
                skipped_line_no.append("Fila: "+ str(ncounter -1) + "El valor del nombre/codigo de la variable esta vacio.") 
            if sheet.cell(r,2).value not in(None,""):
                amount = sheet.cell(r,2).value
                vals.update({
                    'amount': amount 
                })
            lines.append(vals)
        if skipped_line_no:
            raise ValidationError(str(skipped_line_no))
        if self.method == 'create':
            pay_inputs.unlink()
            wizard_lines.create(lines)
        elif self.method == 'update':
            grouped_lines = {}
            for line in lines:
                key = (line['payslip_id'], line['input_type_id'])  # Group by both payslip and input type
                if key in grouped_lines:
                    grouped_lines[key]['amount'] += line['amount']
                else:
                    grouped_lines[key] = line
            # Compare against pay_inputs and update existing records
            for key, line in grouped_lines.items():
                payslip_id, input_type_id = key
                existing_input = pay_inputs.filtered(lambda p: p.payslip_id.id == payslip_id and p.input_type_id.id == input_type_id)
                if existing_input:
                    # Update the amount for existing input
                    existing_input.write({'amount': line['amount']})
                else:
                    # Create new input if no match found
                    wizard_lines.create(line)
        else:
            raise ValidationError("Debe elegir un metodo de importacion de datos")



class WorkEntryWizardPayslip(models.TransientModel):
    _name = 'work.entry.wizard.payslips'
    _description = 'Store the employes to create records in payslips'

    wizard_id = fields.Many2one('work.entry.wizard')
    payslip_run_id = fields.Many2one('hr.payslip.run', string="Lote")
    payslip_id = fields.Many2one('hr.payslip', string="Recibo")
    workline_id = fields.Many2one('hr.payslip.worked_days', string="Linea de entrada")
    work_entry_type_id = fields.Many2one('hr.work.entry.type', string="Tipo de entrada")
    name = fields.Char(string="Nombre", related='work_entry_type_id.name')
    number_of_days = fields.Float(string="Dias")
    number_of_hours = fields.Float(string="Horas")

