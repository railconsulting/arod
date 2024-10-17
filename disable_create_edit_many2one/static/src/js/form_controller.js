/** @odoo-module **/


const { onWillStart, useSubEnv } = owl;
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import session from 'web.session';

patch(FormController.prototype, 'disable_create_edit_many2one.FormController', {
    setup() {
        onWillStart(async () => {
            this.can_create_edit = await session.user_has_group('disable_create_edit_many2one.create_edit_many2one_group');
        });
        useSubEnv({
            can_create_edit: () => this._can_create_edit(),
        });

        this._super(...arguments);
    },
    _can_create_edit() {
        return this.can_create_edit;
    },
});

