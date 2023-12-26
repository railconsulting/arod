# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrDepAccountDebit(models.Model):
    _name = 'hr.department.account'
    _description = 'Account configuration '
    _sql_constraints = [ 
        ('unique_rule',
        'unique(rule_id, account_id, analytic_account_id)',
        'No puedes configurar un mismo centro de costo para una misa regla de salarios')
    ]
    name = fields.Char('Nombre')
    display_type = fields.Selection([
                            ('line_section', "Seccion"),
                            ('line_note', "Nota")], default=False, 
                            help="Technical field for UX purpose.")
    sequence = fields.Integer('Sequence')
    department_id = fields.Many2one('hr.department')
    rule_id = fields.Many2one('hr.salary.rule')
    debit_account_id = fields.Many2one('account.account', string='Debito', company_dependent=True, domain=[('deprecated', '=', False)])
    credit_account_id = fields.Many2one('account.account', string='Credito', company_dependent=True, domain=[('deprecated', '=', False)])
