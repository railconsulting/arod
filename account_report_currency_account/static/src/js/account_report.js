odoo.define('account_report_currency_account.account_report_currency_account', function (require) {
  
    'use strict';

    var accountReportsWidget = require('account_reports.account_report');
    var M2MFilters = accountReportsWidget.M2MFilters;
    // Extender el widget existente
    var core = require('web.core');
var datepicker = require('web.datepicker');
var session = require('web.session');
var field_utils = require('web.field_utils');
var { WarningDialog } = require("@web/legacy/js/_deprecated/crash_manager_warning_dialog");
var QWeb = core.qweb;
var _t = core._t;

    accountReportsWidget.accountReportsWidget.include({
        custom_events: _.extend({}, accountReportsWidget.accountReportsWidget.prototype.custom_events, {
            // Add new change filters events
            'currency_filter_changed': function (ev) {
                var self = this;
                self.report_options.currency_filter = ev.data.res_currency;
                console.log( ev.data.res_currency)
                return self.reload().then(function () {
                    self.$searchview_buttons.find('.account_currency_filter').click();
                });
            },
            'account_filter_changed': function (ev) {
                var self = this;
                self.report_options.account_filter = ev.data.account_account;
                
                return self.reload().then(function () {
                    self.$searchview_buttons.find('.account_account_filter').click();
                });
            },
        }),


        render_searchview_buttons: function() {
         
            var self = this;
            // bind searchview buttons/filter to the correct actions
            var $datetimepickers = this.$searchview_buttons.find('.js_account_reports_datetimepicker');
            var options = { // Set the options for the datetimepickers
                locale : moment.locale(),
                format : 'L',
                icons: {
                    date: "fa fa-calendar",
                },
            };
            // attach datepicker
            $datetimepickers.each(function () {
                var name = $(this).find('input').attr('name');
                var defaultValue = $(this).data('default-value');
                $(this).datetimepicker(options);
                var dt = new datepicker.DateWidget(options);
                dt.replace($(this)).then(function () {
                    dt.$el.find('input').attr('name', name);
                    if (defaultValue) { // Set its default value if there is one
                        dt.setValue(moment(defaultValue));
                    }
                });
            });
            // format date that needs to be show in user lang
            _.each(this.$searchview_buttons.find('.js_format_date'), function(dt) {
                var date_value = $(dt).html();
                $(dt).html((new moment(date_value)).format('ll'));
            });
            // fold all menu
            this.$searchview_buttons.find('.js_foldable_trigger').click(function (event) {
                $(this).toggleClass('o_closed_menu o_open_menu');
                self.$searchview_buttons.find('.o_foldable_menu[data-filter="'+$(this).data('filter')+'"]').toggleClass('o_closed_menu');
            });
            // render filter (add selected class to the options that are selected)
            _.each(self.report_options, function(k) {
                if (k!== null && k.filter !== undefined) {
                    self.$searchview_buttons.find('[data-filter="'+k.filter+'"]').addClass('selected');
                }
            });
            _.each(this.$searchview_buttons.find('.js_account_report_bool_filter'), function(k) {
                $(k).toggleClass('selected', self.report_options[$(k).data('filter')]);
            });
            _.each(this.$searchview_buttons.find('.js_account_report_choice_filter'), function(k) {
                $(k).toggleClass('selected', (_.filter(self.report_options[$(k).data('filter')], function(el){return ''+el.id == ''+$(k).data('id') && el.selected === true;})).length > 0);
            });
            _.each(this.$searchview_buttons.find('.js_account_report_journal_choice_filter'), function(el) {
                var $el = $(el);
                var options = _.filter(self.report_options.journals, function(item){
                    return item.model == $el.data('model') && item.id.toString() == $el.data('id');
                });
                if(options.length > 0){
                    let option = options[0];
                    if(option.selected){
                        el.classList.add('selected');
                    }else{
                        el.classList.remove('selected');
                    }
                }
            });
            $('.js_account_report_journal_choice_filter', this.$searchview_buttons).click(function () {
                var $el = $(this);
    
                // Change the corresponding element in option.
                var options = _.filter(self.report_options.journals, function(item){
                    return item.model == $el.data('model') && item.id.toString() == $el.data('id');
                });
                if(options.length > 0){
                    let option = options[0];
                    option.selected = !option.selected;
                }
    
                // Specify which group has been clicked.
                if($el.data('model') == 'account.journal.group'){
                    if($el.hasClass('selected')){
                        self.report_options.__journal_group_action = {'action': 'remove', 'id': parseInt($el.data('id'))};
                    }else{
                        self.report_options.__journal_group_action = {'action': 'add', 'id': parseInt($el.data('id'))};
                    }
                }
                self.reload();
            });
            _.each(this.$searchview_buttons.find('.js_account_reports_one_choice_filter'), function(k) {
                let menu_data = $(k).data('id');
                let option_data = self.report_options[$(k).data('filter')];
                $(k).toggleClass('selected', option_data == menu_data);
            });
            // click events
            this.$searchview_buttons.find('.js_account_report_date_filter').click(function (event) {
                self.report_options.date.filter = $(this).data('filter');
                var error = false;
                if ($(this).data('filter') === 'custom') {
                    var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from"]');
                    var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to"]');
                    if (date_from.length > 0){
                        error = date_from.val() === "" || date_to.val() === "";
                        self.report_options.date.date_from = field_utils.parse.date(date_from.val());
                        self.report_options.date.date_to = field_utils.parse.date(date_to.val());
                    }
                    else {
                        error = date_to.val() === "";
                        self.report_options.date.date_to = field_utils.parse.date(date_to.val());
                    }
                }
                if (error) {
                    new WarningDialog(self, {
                        title: _t("Odoo Warning"),
                    }, {
                        message: _t("Date cannot be empty")
                    }).open();
                } else {
                    self.reload();
                }
            });
            this.$searchview_buttons.find('.js_account_report_bool_filter').click(function (event) {
                var option_value = $(this).data('filter');
                self.report_options[option_value] = !self.report_options[option_value];
                if (option_value === 'unfold_all') {
                    self.unfold_all(self.report_options[option_value]);
                }
                self.reload();
            });
    
            this.$searchview_buttons.find('.js_account_report_choice_filter').click(function (event) {
                var option_value = $(this).data('filter');
                var option_id = $(this).data('id');
                _.filter(self.report_options[option_value], function(el) {
                    if (''+el.id == ''+option_id){
                        if (el.selected === undefined || el.selected === null){el.selected = false;}
                        el.selected = !el.selected;
                    } else if (option_value === 'ir_filters') {
                        el.selected = false;
                    }
                    return el;
                });
                self.reload();
            });
            const rateHandler = function (event) {
                let optionValue = $(this).data('filter');
                if (optionValue === 'current_currency') {
                    delete self.report_options.currency_rates;
                } else if (optionValue === 'custom_currency') {
                    _.each($('input.js_account_report_custom_currency_input'), (input) => {
                        self.report_options.currency_rates[input.name].rate = input.value;
                    });
                }
                self.reload();
            };
            $(document).on('click', '.js_account_report_custom_currency', rateHandler);
            $(document).on('click', '.js_account_report_custom_currency', rateHandler);
            this.$searchview_buttons.find('.js_account_report_custom_currency').click(rateHandler);
            this.$searchview_buttons.find('.js_account_reports_one_choice_filter').click(function (event) {
                var option_value = $(this).data('filter');
                self.report_options[option_value] = $(this).data('id');
    
                if (option_value === 'tax_unit') {
                    // Change the currently selected companies depending on the chosen tax_unit option
                    // We need to do that to prevent record rules from accepting records that they shouldn't when generating the report.
    
                    var main_company = session.user_context.allowed_company_ids[0];
                    var companies = [main_company];
    
                    if (self.report_options['tax_unit'] != 'company_only') {
                        var unit_id = self.report_options['tax_unit'];
                        var selected_unit = self.report_options['available_tax_units'].filter(unit => unit.id == unit_id)[0];
                        companies = selected_unit.company_ids;
                    }
                    self.persist_options_for_company_reload(companies); // So that previous_options are kept after the reload performed by setCompanies
                    session.setCompanies(main_company, companies);
                }
                else {
                    self.reload();
                }
            });
            this.$searchview_buttons.find('.js_account_report_date_cmp_filter').click(function (event) {
                self.report_options.comparison.filter = $(this).data('filter');
                var error = false;
                var number_period = $(this).parent().find('input[name="periods_number"]');
                self.report_options.comparison.number_period = (number_period.length > 0) ? parseInt(number_period.val()) : 1;
                if ($(this).data('filter') === 'custom') {
                    var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from_cmp"]');
                    var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to_cmp"]');
                    if (date_from.length > 0) {
                        error = date_from.val() === "" || date_to.val() === "";
                        self.report_options.comparison.date_from = field_utils.parse.date(date_from.val());
                        self.report_options.comparison.date_to = field_utils.parse.date(date_to.val());
                    }
                    else {
                        error = date_to.val() === "";
                        self.report_options.comparison.date_to = field_utils.parse.date(date_to.val());
                    }
                }
                if (error) {
                    new WarningDialog(self, {
                        title: _t("Odoo Warning"),
                    }, {
                        message: _t("Date cannot be empty")
                    }).open();
                } else {
                    self.reload();
                }
            });
    
            // partner filter
            if (this.report_options.partner) {
                if (!this.partners_m2m_filter) {
                    var fields = {};
                    if ('partner_ids' in this.report_options) {
                        fields['partner_ids'] = {
                            label: _t('Partners'),
                            modelName: 'res.partner',
                            value: this.report_options.partner_ids.map(Number),
                        };
                    }
                    if ('partner_categories' in this.report_options) {
                        fields['partner_categories'] = {
                            label: _t('Tags'),
                            modelName: 'res.partner.category',
                            value: this.report_options.partner_categories.map(Number),
                        };
                    }
                    if (!_.isEmpty(fields)) {
                        this.partners_m2m_filter = new M2MFilters(this, fields, 'partner_filter_changed');
                        this.partners_m2m_filter.appendTo(this.$searchview_buttons.find('.js_account_partner_m2m'));
                    }
                } else {
                    this.$searchview_buttons.find('.js_account_partner_m2m').append(this.partners_m2m_filter.$el);
                }
            }
    
            // analytic filter
            if (this.report_options.analytic) {
                if (!this.analytic_m2m_filter) {
                    var fields = {};
                    if (this.report_options.analytic_accounts) {
                        fields['analytic_accounts'] = {
                            label: _t('Accounts'),
                            modelName: 'account.analytic.account',
                            value: this.report_options.analytic_accounts.map(Number),
                        };
                    }
                    if (!_.isEmpty(fields)) {
                        this.analytic_m2m_filter = new M2MFilters(this, fields, 'analytic_filter_changed');
                        this.analytic_m2m_filter.appendTo(this.$searchview_buttons.find('.js_account_analytic_m2m'));
                    }
                } else {
                    this.$searchview_buttons.find('.js_account_analytic_m2m').append(this.analytic_m2m_filter.$el);
                }
            }
            if (this.report_options.analytic_groupby) {
                if (!this.analytic_groupby_m2m_filter) {
                    var fields = {};
                    if (this.report_options.analytic_accounts_groupby) {
                        fields['analytic_accounts_groupby'] = {
                            label: _t('Accounts'),
                            modelName: 'account.analytic.account',
                            value: this.report_options.analytic_accounts_groupby.map(Number),
                        };
                    }
                    if (!_.isEmpty(fields)) {
                        this.analytic_groupby_m2m_filter = new M2MFilters(this, fields, 'analytic_groupby_filter_changed');
                        this.analytic_groupby_m2m_filter.appendTo(this.$searchview_buttons.find('.js_account_analytic_groupby_m2m'));
                    }
                } else {
                    this.$searchview_buttons.find('.js_account_analytic_groupby_m2m').append(this.analytic_groupby_m2m_filter.$el);
                }
            }
    
            //OVERRIDE HERE add new filter with m2m filter adapted
            if (!this.currency_m2m_filter) {
                var fields = {};
                if (this.report_options.res_currency) {
                    fields['res_currency'] = {
                        label: _t('Currency'),
                        modelName: 'res.currency',
                        value: this.report_options.res_currency.map(Number),
                    };
                }
                if (!_.isEmpty(fields)) {
                    this.currency_m2m_filter = new M2MFilters(this, fields, 'currency_filter_changed');
                    this.currency_m2m_filter.appendTo(this.$searchview_buttons.find('.js_account_currency_filter_m2m'));
                }
            } else {
                this.$searchview_buttons.find('.js_account_currency_filter_m2m').append(this.currency_m2m_filter.$el);
            } 
            
            if (!this.account_m2m_filter) {
                var fields = {};
                if (this.report_options.account_account) {
                    fields['account_account'] = {
                        label: _t('Account'),
                        modelName: 'account.account',
                        value: this.report_options.account_account.map(Number),
                    };
                }
                if (!_.isEmpty(fields)) {
                    this.account_m2m_filter = new M2MFilters(this, fields, 'account_filter_changed');
                    this.account_m2m_filter.appendTo(this.$searchview_buttons.find('.js_account_account_filter_m2m'));
                }
            } else {
                this.$searchview_buttons.find('.js_account_account_filter_m2m').append(this.account_m2m_filter.$el);
            } 
            
            if (this.report_options.analytic_plan_groupby) {
                if (!this.analytic_plan_groupby_m2m_filter) {
                    var fields = {};
                    if (this.report_options.analytic_plans_groupby) {
                        fields['analytic_plans_groupby'] = {
                            label: _t('Plans'),
                            modelName: 'account.analytic.plan',
                            value: this.report_options.analytic_plans_groupby.map(Number),
                        };
                    }
                    if (!_.isEmpty(fields)) {
                        this.analytic_plan_groupby_m2m_filter = new M2MFilters(this, fields, 'analytic_plans_groupby_filter_changed');
                        this.analytic_plan_groupby_m2m_filter.appendTo(this.$searchview_buttons.find('.js_account_analytic_plans_groupby_m2m'));
                    }
                } else {
                    this.$searchview_buttons.find('.js_account_analytic_plans_groupby_m2m').append(this.analytic_plan_groupby_m2m_filter.$el);
                }
            }
        },
       
        


    });
    
});
/** Registra el componente con el patch aplicado */
