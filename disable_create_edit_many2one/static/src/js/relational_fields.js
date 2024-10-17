/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { PropertyValue } from "@web/views/fields/properties/property_value";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";

const { onWillStart } = owl;
import session from 'web.session';

patch(Many2XAutocomplete.prototype, "disable_create_edit_many2one.Many2XAutocomplete", {
    setup() {
        this._super(...arguments);
        if (this.env.can_create_edit !== undefined && !this.env.can_create_edit()) {
            this.activeActions.createEdit = false;
            this.activeActions.create = false;
        }
    },

    async loadOptionsSource(request) {
        if (this.env.can_create_edit !== undefined && !this.env.can_create_edit()) {
            this.activeActions.createEdit = false;
            this.activeActions.create = false;
        }
        return this._super(...arguments);
    },
});

patch(Many2OneField.prototype, "disable_create_edit_many2one.Many2OneField", {
    setup() {

        if (this.env.can_create_edit !== undefined && !this.env.can_create_edit()) {
            this.props.canQuickCreate = false;
            this.props.canCreate = false;
            this.props.canCreateEdit = false;
        }
        this._super(...arguments);
    },
});

patch(Many2ManyTagsField.prototype, 'disable_create_edit_many2one.Many2ManyTagsField', {
    setup() {

        if (this.env.can_create_edit !== undefined && !this.env.can_create_edit()) {
            this.props.canQuickCreate = false;
            this.props.canCreate = false;
            this.props.canCreateEdit = false;
        }
        this._super(...arguments);
    },
});
