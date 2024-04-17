# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    fe_code = fields.Char(
        string='FE Codigo',
        help='Codigo de la empresa para la facturación electroica'
    )
