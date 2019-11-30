# -*- coding: utf-8 -*-
{
    'name': "Stock transfer",

    'summary': """
        Stock transfer warehouse
        """,

    'description': """
    """,
    # tiendz
    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock','web','stock_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/stock_warehouse.xml',
        'views/stock_transfer_from_view.xml',
        'views/stock_transfer_to_view.xml',
        'views/stock_transfer_line.xml',
        'report/stock_report.xml',
        'views/inherit_category_product_view.xml'
    ],
}
