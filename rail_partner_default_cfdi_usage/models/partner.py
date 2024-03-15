# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    uso_cfdi = fields.Selection(
        selection=[('G01', 'Adquisición de mercancías'),
                   ('G02', 'Devoluciones, descuentos o bonificaciones'),
                   ('G03', 'Gastos en general'),
                   ('I01', 'Construcciones'),
                   ('I02', 'Mobiliario y equipo de oficina por inversiones'),
                   ('I03', 'Equipo de transporte'),
                   ('I04', 'Equipo de cómputo y accesorios'),
                   ('I05', 'Dados, troqueles, moldes, matrices y herramental'),
                   ('I06', 'Comunicacion telefónica'),
                   ('I07', 'Comunicación Satelital'),
                   ('I08', 'Otra maquinaria y equipo'),
                   ('D01', 'Honorarios médicos, dentales y gastos hospitalarios'),
                   ('D02', 'Gastos médicos por incapacidad o discapacidad'),
                   ('D03', 'Gastos funerales'),
                   ('D04', 'Donativos'),
                   ('D07', 'Primas por seguros de gastos médicos'),
                   ('D08', 'Gastos de transportación escolar obligatoria'),
                   ('D10', 'Pagos por servicios educativos (colegiaturas)'),
                   ('P01', 'Por definir'),
                   ('S01', 'Sin efectos fiscales'),
                   ('CP01', 'Pagos'),
                   ('CN01', 'Nomina'),
                   ],
        string=('Uso CFDI (cliente)'),
    )    
