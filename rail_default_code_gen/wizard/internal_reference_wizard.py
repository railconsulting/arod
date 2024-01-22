# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields


class InternalReferenceWizard(models.TransientModel):
    _name = 'internal.reference.wizard'
    _description = "Internal Reference Wizard"

    replace_existing = fields.Boolean(string="Replace Existing ?")

    def action_generate_reference(self):
        product_sequence_name = ''
        product_sequence_attribute = ''
        product_sequence_category = ''
        product_sequence_seq = ''
        company_id = self.env.company
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_model = context.get('active_model', []) or []
        search_domain_for_product = []
        if active_model == 'product.template':
            search_domain_for_product.append(('id', 'in', active_ids))
        elif active_model == 'product.product':
            search_domain_for_product.append(('id', 'in', active_ids))
        if active_model == 'product.template':
            for template in self.env['product.template'].browse(active_ids):
                product_template_sequence = ''

                if self.replace_existing:
        
                    
                    if company_id.product_sequence_config and company_id.product_sequence:
                        sequence = self.env['ir.sequence'].next_by_code(company_id.product_sequence.code)
                        product_template_sequence += str(sequence)
                        product_sequence_seq= product_template_sequence            
                    
                    seq_list=[]
                    seq_name_list=[]
                    if product_sequence_seq :
                        seq_list.append(self.env.company.product_sequence_seq)
                        seq_name_list.append(product_sequence_seq)
                    
                    zipped_pairs = zip(seq_list, seq_name_list)
        
                    result_seq_name_list = [x for _, x in sorted(zipped_pairs)]     
                    product_code_str = ''.join([str(elem) for elem in result_seq_name_list])                
                    if product_code_str.endswith(str(self.env.company.product_sequence_separate)):
                        product_code_str = product_code_str[:-1]
                    if product_code_str != '':
                        template.sudo().write({
                            'default_code': product_code_str,
                        })
                    
                    
                else:
                    if not template.default_code:
                        product_name = str(template.name)
                        product_template_sequence='' 

                        if company_id.product_sequence_config and company_id.product_sequence:
                            sequence = self.env['ir.sequence'].next_by_code(company_id.product_sequence.code)
                            product_template_sequence += str(sequence)
                            product_sequence_seq=product_template_sequence
                        
                        seq_list=[]
                        seq_name_list=[]
                        if product_sequence_seq :
                            seq_list.append(self.env.company.product_sequence_seq)
                            seq_name_list.append(product_sequence_seq)
                        
                        zipped_pairs = zip(seq_list, seq_name_list)
            
                        result_seq_name_list = [x for _, x in sorted(zipped_pairs)]     
                        product_code_str = ''.join([str(elem) for elem in result_seq_name_list])                
                        if product_code_str.endswith(str(self.env.company.product_sequence_separate)):
                            product_code_str = product_code_str[:-1]
                        if product_code_str != '':
                            template.sudo().write({
                                'default_code': product_code_str,
                            })
                        
                        
        elif active_model == 'product.product' or active_model == 'res.config.settings':
            for product in self.env['product.product'].sudo().search(search_domain_for_product):
                product_sequence = ''
                if self.replace_existing:
                    if company_id.product_sequence_config and company_id.product_sequence:
                        sequence = self.env['ir.sequence'].next_by_code(company_id.product_sequence.code)
                        product_sequence += str(sequence)
                        product_sequence_seq=product_sequence
                    
                    seq_list=[]
                    seq_name_list=[]
                    if product_sequence_seq :
                        seq_list.append(self.env.company.product_sequence_seq)
                        seq_name_list.append(product_sequence_seq)
                    
                    zipped_pairs = zip(seq_list, seq_name_list)
                    result_seq_name_list = [x for _, x in sorted(zipped_pairs)]     
                    product_code_str = ''.join([str(elem) for elem in result_seq_name_list])                
                    if product_code_str.endswith(str(self.env.company.product_sequence_separate)):
                        product_code_str = product_code_str[:-1]
                    if product_code_str != '':
                        product.sudo().write({
                            'default_code': product_code_str,
                        })
                    
                else:
                    if not product.default_code:
                        product_name = str(product.name)
                        if int(company_id.product_name_digit) >= 1:
                            product_name = product_name[:int(
                                company_id.product_name_digit)]

                            product_sequence_name=product_sequence
                                    
                        product_sequence='' 
                        
                        if company_id.product_sequence_config and company_id.product_sequence:
                            sequence = self.env['ir.sequence'].next_by_code(company_id.product_sequence.code)
                            product_sequence += str(sequence)
                            product_sequence_seq=product_sequence
                        
                        seq_list=[]
                        seq_name_list=[]
                        if product_sequence_seq :
                            seq_list.append(self.env.company.product_sequence_seq)
                            seq_name_list.append(product_sequence_seq)
                        
                        zipped_pairs = zip(seq_list, seq_name_list)
            
                        result_seq_name_list = [x for _, x in sorted(zipped_pairs)]     
                        product_code_str = ''.join([str(elem) for elem in result_seq_name_list])                
                        if product_code_str.endswith(str(self.env.company.product_sequence_separate)):
                            product_code_str = product_code_str[:-1]
                        if product_code_str != '':
                            product.sudo().write({
                                'default_code': product_code_str,
                            })