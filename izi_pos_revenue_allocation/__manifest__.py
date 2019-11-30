# -*- coding: utf-8 -*-
{
    'name': "Pos Revenue Allocation",

    'summary': """
        Phân bổ doanh thu đơn hàng""",

    'description': """
        Phân bổ doanh thu đơn hàng
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_pos', 'point_of_sale', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/pos_revenue_security_view.xml',
        'views/pos_revenue_allocation_view.xml',
        'views/pos_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}