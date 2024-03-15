# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.depends('move_raw_ids','workorder_ids')
    def _get_totals(self):
        for r in self:
            material_total = labour_total = wo_total = total = 0
            for p in r.move_raw_ids:
                material_total += p.price_unit
            for wo in r.workorder_ids:
                times = wo.time_ids
                if times:
                    for t in times:
                        labour_total += round(wo.workcenter_id.employee_costs_hour * (t.duration / 60), 2)
                wo_total += round(wo.workcenter_id.costs_hour * (wo.duration / 60),2)
            total = material_total + labour_total + wo_total

            r.update({
                'total_material_cost': material_total,
                'total_labour_emp_cost': labour_total,
                'total_labour_wo_cost': wo_total,
                'total_cost': total,
            })


    total_material_cost = fields.Float(string="Total materiales", compute='_get_totals')
    total_labour_emp_cost = fields.Float(string="Total mano de obra", compute='_get_totals')
    total_labour_wo_cost = fields.Float(string="Total centro de trabajo", compute='_get_totals')
    total_cost = fields.Float(string="Total general", compute='_get_totals')