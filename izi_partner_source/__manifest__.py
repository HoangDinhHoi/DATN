# -*- coding: utf-8 -*-
{
    'name': "Partner Source",

    'summary': """Quản lý nguồn khách hàng""",

    'description': """""",

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customer Relationship Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_partner'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/partner_source.xml',
    ],
    # only loaded in demonstration mode
    'demo': []
}