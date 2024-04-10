# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def cr_logout(self):
        request.session['employee_id'] = False
        return True
