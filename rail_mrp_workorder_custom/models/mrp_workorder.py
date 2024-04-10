
# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import ValidationError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    employee_costs_hour = fields.Float("Costo por empleado")

    def button_finish(self):
        res = super(MrpWorkorder, self).button_finish()
        for workorder in self:
            append_vals = {
                'employee_costs_hour': workorder.workcenter_id.employee_costs_hour
            }
            workorder.write(append_vals)
        
        return res


    def cr_check_employee_is_in_another_workorder(self,employee_id):
        employee_workorder = self.search([('id','!=',self.id),('employee_ids','in',employee_id)])
        return bool(employee_workorder)

    def button_start(self):
        res = super(MrpWorkorder, self).button_start
        all_available = True
        if self.move_raw_ids.filtered(lambda x: x.reserved_availability <= 0):
            all_available = False
        if not all_available:
            raise ValidationError("No puedes iniciar la orden de produccion debido a que no todos los productos estan disponibles")
        
        return res