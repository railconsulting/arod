# -*- coding: utf-8 -*-
{
    "name": "Product Internal Reference Generator",
    "author": "Rail / Kevin Lopez",
    "website": "https://www.rail.com.mx",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Internal Reference Generator",
    "version": "16.0.0.1",
    "depends": [
        "sale_management",
        "account",
        "product",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        'data/product_prefix.xml',
        "views/product.xml",
        "views/product_prefix.xml",
        "views/res_config_setting.xml",
        "wizard/internal_reference_wizard.xml",
    ],
    "application": True,
    "installable": True,
}
