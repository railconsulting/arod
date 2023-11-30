# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class WorkEntryWizard(models.TransientModel):
    _name = 'work.entry.wizard'
    _description = 'Batch entries recording'

    payslip_run_id = fields.Many2one('hr.payslip.run')
    work_entry_type_id = fields.Many2one('hr.work.entry.type')
    input_type_id = fields.Many2one('hr.payslip.input.type')
    work_payslip_ids = fields.One2many('work.entry.wizard.payslips','wizard_id')
    input_payslip_ids = fields.One2many('input.entry.wizard.payslips','wizard_id')
    hide = fields.Boolean('Hide')

    def get_work_payslips(self):
        if self.work_entry_type_id and self.payslip_run_id:
            self.hide = True
            work_lines_object = self.env['work.entry.wizard.payslips']
            #delete existing lines
            del_lines = work_lines_object.search([('wizard_id','=',self.id),('work_entry_type_id','=',self.work_entry_type_id.id)])
            if del_lines:
                for l in del_lines:
                    l.unlink()
            payslips = self.env['hr.payslip'].search([('payslip_run_id','=', self.payslip_run_id.id)])
            for r in payslips:
                work_lines = work_lines_object.create({
                    'wizard_id': self.id,
                    'payslip_run_id': self.payslip_run_id.id,
                    'payslip_id': r.id,
                    'work_entry_type_id': self.work_entry_type_id.id,
                    'name': self.work_entry_type_id.name,
                    'number_of_days': 0.00,
                    'number_of_hours': 0.00,
                })
        else:
            raise ValidationError(_("Please, first select a work entry"))
        return {
            'name': 'Record work entries',
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,                
        }

    def get_input_payslips(self):
        if self.input_type_id and self.payslip_run_id:
            self.hide = True
            input_lines_object = self.env['input.entry.wizard.payslips']
            #delete existing lines
            del_lines = input_lines_object.search([('wizard_id','=',self.id),('input_type_id','=',self.input_type_id.id)])
            if del_lines:
                for l in del_lines:
                    l.unlink()
            payslips = self.env['hr.payslip'].search([('payslip_run_id','=', self.payslip_run_id.id)])
            for r in payslips:
                input_lines = input_lines_object.create({
                    'wizard_id': self.id,
                    'payslip_run_id': self.payslip_run_id.id,
                    'payslip_id': r.id,
                    'input_type_id': self.input_type_id.id,
                    'name': self.input_type_id.name,
                    'amount': 0.00,                
                })
        else:
            raise ValidationError(_("Please, first select an input"))
        return {
            'name': 'Record work entries',
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
            input_entry_object = self.env['hr.payslip.input']
            if self.work_payslip_ids:
                for r in self.work_payslip_ids.filtered(lambda x:x.number_of_days > 0):
                    work_line = work_entry_object.create({
                        'code': r.work_entry_type_id.code,
                        'contract_id': r.payslip_id.contract_id.id,
                        'name': r.work_entry_type_id.code,
                        'number_of_days': r.number_of_days,
                        'number_of_hours': r.number_of_hours,
                        'payslip_id': r.payslip_id.id,
                        'work_entry_type_id': r.work_entry_type_id.id
                    })
            if self.input_payslip_ids:
                for r in self.input_payslip_ids.filtered(lambda x:x.amount > 0):
                    input_line = input_entry_object.create({
                        'code': r.input_type_id.code,
                        'contract_id': r.payslip_id.contract_id.id,
                        'name': r.input_type_id.name,
                        'payslip_id': r.payslip_id.id,
                        'input_type_id': r.input_type_id.id,
                        'amount': r.amount,
                    })
        else:
            raise ValidationError(_("Before confirm you need get some payslips"))


class WorkEntryWizardPayslip(models.TransientModel):
    _name = 'work.entry.wizard.payslips'
    _description = 'Store the employes to create records in payslips'

    wizard_id = fields.Many2one('work.entry.wizard')
    payslip_run_id = fields.Many2one('hr.payslip.run')
    payslip_id = fields.Many2one('hr.payslip')
    work_entry_type_id = fields.Many2one('hr.work.entry.type')
    name = fields.Char(string="Nombre", related='work_entry_type_id.name')
    number_of_days = fields.Float('Days')
    number_of_hours = fields.Float('Hours')

class InputEntryWizardPayslip(models.TransientModel):
    _name = 'input.entry.wizard.payslips'
    _description = 'Store the employees to create records in payslips'

    wizard_id = fields.Many2one('work.entry.wizard')
    payslip_run_id = fields.Many2one('hr.payslip.run')
    payslip_id = fields.Many2one('hr.payslip')
    input_type_id = fields.Many2one('hr.payslip.input.type')
    name = fields.Char(string="Nombre", related='input_type_id.name')
    amount = fields.Float('Amount')

