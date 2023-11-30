/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { AccountPaymentField } from "@account/components/account_payment_field/account_payment_field";

export class AccountPaymentFieldPartial extends AccountPaymentField {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }
    async partialOutstandingCredit(id) {
        this.action.doAction({
            name: 'Aplicacion pago parcial',
            type: 'ir.actions.act_window',
            res_model: 'partial.payment.wizard',
            views: [[false, 'form']],
            target: 'new',
            context: {'line_id': id, 'move_id': this.move_id},
        });
    }

}
registry.category("fields").add("payment", AccountPaymentFieldPartial, { force: true });
