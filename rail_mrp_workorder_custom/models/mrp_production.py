# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    pre_move_raw_ids = fields.One2many(
        'stock.move', 'raw_material_production_id', 'Components',
        compute='_compute_move_raw_ids', store=True,
        copy=False,
        domain=[('scrapped', '=', False)])
    
    pre_workorder_ids = fields.One2many(
        'mrp.workorder', 'production_id', 'Work Orders', copy=False,
        compute='_compute_workorder_ids', store=True,)
    
    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        zero_cost_list = zero_qty_list = []
        for p in self.move_raw_ids.filtered(lambda x: x.product_id.standard_price == 0):
            zero_cost_list.append(p.product_id.display_name)
        for p in self.move_raw_ids.filtered(lambda x: x.product_qty == 0):
            zero_qty_list.append(p.product_id.display_name)
        message = ""
        if self.move_raw_ids.filtered(lambda x: x.product_qty == 0):
            message += "Los siguientes productos no tienen una cantidad establecida para finalizar la orden: \n"
            message += str(zero_qty_list)
        if self.move_raw_ids.filtered(lambda x: x.product_id.standard_price == 0):
            message += "\n Los siguientes productos no tienen un costo establecido para finalizar la orden: \n"
            message += str(zero_cost_list)

        if self.move_raw_ids.filtered(lambda x: x.product_qty == 0) or self.move_raw_ids.filtered(lambda x: x.product_id.standard_price == 0):
            raise ValidationError(message)

        return res

    @api.depends('move_raw_ids','workorder_ids')
    def _get_totals(self):
        for r in self:
            material_total = labour_total = wo_total = total = 0
            for p in r.move_raw_ids:
                if p.product_qty == 0:
                    qty = p.product_uom_qty
                else:
                    qty = p.product_qty
                material_total += p.price_unit * qty
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