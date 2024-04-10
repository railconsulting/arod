# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpWorkCenter(models.Model):
    _inherit = 'mrp.workcenter'

    inventory_account_id = fields.Many2one('account.account', string="Cuenta produccion en proceso", required=True)
    expense_account_id = fields.Many2one('account.account', string="Cuenta gasto", required=True)

    standard_employee_cost = fields.Boolean(string="Costo estandar", help="Al estar activo obtendra el costo por hora desde el centro de trabajo y no desde los empleados")

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    @api.depends('duration')
    def _compute_cost(self):
        for time in self:
            if time.employee_id and not time.workcenter_id.standard_employee_cost:
                time.employee_cost = time.employee_id.hourly_cost
                time.total_cost = time.employee_cost * time.duration / 60
            else:
                hour_cost = time.workcenter_id.employee_costs_hour
                time.employee_cost = hour_cost
                time.total_cost = hour_cost * time.duration / 60