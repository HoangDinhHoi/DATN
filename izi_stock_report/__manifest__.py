# -*- coding: utf-8 -*-
{
    'name': "Stock report",

    'summary': """
        Stock Report
        """,

    'description': """
        Stock Report
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','stock_account', 'uom','izi_branch'],

    # always loaded
    'data': [
        'views/invisible_report_inventory_default_core.xml',
        'security/ir.model.access.csv',
        'report/internal_template.xml',
        'report/stock_report_qweb_menu.xml',
        'report/stock_report_qweb_incoming.xml',
        'report/stock_report_qweb_outgoing.xml',
        # 'views/rpt_stock_inventory.xml',
        # 'views/rpt_stock_inventory_value.xml',
        # 'views/rpt_stock_inventory_in_and_out.xml',
        'views/rpt_stock_location_in_out.xml',
        'views/rpt_stock_delivery.xml',
        'views/rpt_stock.xml',
    ],
}