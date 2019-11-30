# -*- coding: utf-8 -*-
{
    'name': "Sale order",

    'summary': """Quản lý đơn hàng""",

    'description': """Quản lý đơn hàng""",

    'author': "Izisolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'crm', 'point_of_sale', 'izi_branch', 'sale_crm', 'sale_management',
                'izi_message_dialog', 'izi_crm_booking'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/sale_order_sequence.xml',
        'views/crm_lead.xml',
        'wizards/sale_order_make_pos_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}