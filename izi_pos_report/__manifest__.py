# -*- coding: utf-8 -*-
{
    'name': "Pos report",

    'summary': """
        Pos report
        """,

    'description': """
        Pos report
        """,

    'author': "HoiHD",
    'website': "http://www.fb.com/hoihandsome",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos'],

    # always loaded
    'data': [
        'report/internal_template.xml',
        'report/template_report_bill.xml',
        'report/template_report_session.xml',
        'report/report_case_session.xml',
        'report/menu.xml',
    ],
}
