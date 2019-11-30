# -*- coding: utf-8 -*-
{
    'name': "POS Use Service",

    'summary': """
        - Use service or redeeem card service
        """,

    'description': """
        - Use service or redeeem card service
    """,

    'author': "HoiHD",
    'website': "http://www.fb.com/hoihandsome",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'product', 'stock', 'hr', 'izi_pos'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/pos_use_service_security.xml',
        'views/pos_config_view.xml',
        'data/ir_sequence_data.xml',
        'views/product_template_view.xml',
        'views/pos_use_service_view.xml',
        'views/pos_use_service_product.xml',
        'views/pos_material_request_view.xml',
        'views/pos_material_request_product.xml',
        'wizard/pos_use_service_compare_transient.xml',
        'report/report_retail_service.xml',
        'views/action_report_request_material.xml',
        'views/material_request_report.xml',
    ],
}
