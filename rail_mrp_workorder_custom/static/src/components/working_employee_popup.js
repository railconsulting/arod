/** @odoo-module **/

import { WorkingEmployeePopup } from "@mrp_workorder_hr/components/working_employee_popup";
import { patch } from 'web.utils';
import Tablet from '@mrp_workorder/components/tablet';

patch(Tablet.prototype, 'cr_mrp_workorder_hr', {
    async startEmployee(employeeId, pin) {
        const superMethod = this._super.bind(this);
        let employee_is_in_another_workorder = await this.orm.call(
            'mrp.workorder',
            'cr_check_employee_is_in_another_workorder',
            [this.workorderId, employeeId],
        );
        if (employee_is_in_another_workorder) {
            this.notification.add(this.env._t('El empleado ya esta registrado en otra orden de trabajo!!!'), {type: 'danger'});
            this.actionRedirect = this.startEmployee;
            return
        }
        superMethod(employeeId, pin);
    },
});

export class CrWorkingEmployeePopup extends WorkingEmployeePopup {
    async stopEmployee(employeeId) {
        await this.orm.call(
            'hr.employee', 'cr_logout', [employeeId],);
        await super.stopEmployee(employeeId);
        this.close();
    }

    async startEmployee(employeeId) {        
        await this.orm.call(
            'hr.employee', 'cr_logout', [employeeId],);
        await super.startEmployee(employeeId);
        this.close();
    }
}
Tablet.components.WorkingEmployeePopup = CrWorkingEmployeePopup;
