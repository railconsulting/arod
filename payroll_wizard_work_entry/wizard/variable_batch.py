# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging, xlrd, base64

class WorkEntryWizard(models.TransientModel):
    _name = 'input.entry.wizard'
    _description = 'Batch entries recording'

    payslip_run_id = fields.Many2one('hr.payslip.run', string="Lote")
    input_type_id = fields.Many2one('hr.payslip.input.type', string="Tipo de entrada")
    input_payslip_ids = fields.One2many('input.entry.wizard.payslips','wizard_id', string="lineas")
    record_type = fields.Selection(string="Tipo actualizacion", selection=[
        ('manual','Manual'),
        ('xls','Excel'),
    ], default='manual')
    method = fields.Selection(string="Metodo de importacion", selection=[
        ('create','Borrar y actualizar'),
        ('update','Leer y actualizar'),
    ], default='create')
    xls_file = fields.Binary(string="Archivo Excel")

    def get_input_payslips(self):
        if self.input_type_id and self.payslip_run_id:
            input_lines_object = self.env['input.entry.wizard.payslips']

            payslips = self.env['hr.payslip'].search([('payslip_run_id','=', self.payslip_run_id.id)])
            inputs = self.env['hr.payslip.input'].search([
                ('payslip_id','in', payslips.ids),
                ('input_type_id','=', self.input_type_id.id),
            ])
            wizard_lines = []
            for r in payslips:
                vals = {
                    'wizard_id': self.id,
                    'payslip_run_id': self.payslip_run_id.id,
                    'payslip_id': r.id,
                    'input_type_id': self.input_type_id.id,
                    'name': self.input_type_id.name,
                }
            amount = 0
            for i in inputs:
                if i.payslip_id.id == r.id and self.input_type_id.id == i.input_type_id.id:
                    amount += i.amount
                    vals.update({
                        'inputline_id': i.id
                    })
                vals.update({
                    'amount': amount,
                })
                wizard_lines.append(vals)
            input_lines_object.create(wizard_lines)
        else:
            raise ValidationError(_("Por favor primero elige una variable"))
        return {
            'name': 'Registro de variables',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,                
        }


    def confirm_input_entries(self):
        if self.input_payslip_ids:
            input_entry_object = self.env['hr.payslip.input']
            if self.input_payslip_ids:
                for r in self.input_payslip_ids.filtered(lambda x:x.amount > 0):
                    if r.inputline_id:
                        r.inputline_id.update({
                            'amount': r.amount,
                        })
                    else:
                        input_entry_object.create({
                            'code': r.input_type_id.code,
                            'contract_id': r.payslip_id.contract_id.id,
                            'name': r.input_type_id.name,
                            'payslip_id': r.payslip_id.id,
                            'input_type_id': r.input_type_id.id,
                            'amount': r.amount,
                        })
        else:
            raise ValidationError(_("Primero selecciona algun(os) recibo(s)"))
        
    def download_excel_file(self):
        """For downloading a sample excel file"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/download/inputs_excel',
            'target': 'self',
            'file_name': 'import_inputs_template.xlsx'
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
            #1 Codigo/Nombre input
            #2 Monto
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



class InputEntryWizardPayslip(models.TransientModel):
    _name = 'input.entry.wizard.payslips'
    _description = 'Store the employees to create records in payslips'

    wizard_id = fields.Many2one('input.entry.wizard')
    payslip_run_id = fields.Many2one('hr.payslip.run', string="Lote")
    payslip_id = fields.Many2one('hr.payslip', string="Recibo")
    inputline_id = fields.Many2one('hr.payslip.input', string="Linea de entrada")
    input_type_id = fields.Many2one('hr.payslip.input.type', string="Variable")
    name = fields.Char(string="Nombre", related='input_type_id.name')
    amount = fields.Float(string="Nombre")

