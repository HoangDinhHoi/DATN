# -*- coding: utf-8 -*-
{
    'name': "izi_hr",

    'summary': """
        Additional some field as x_employee_code""",

    'description': """
        Inherit HR Module
    """,

    'author': "HoiHD",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resource',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_recruitment'],

    # always loaded
    'data': [
        'views/hr.xml',
        'views/hr_employee_level.xml',
        'views/hr_job.xml',
        'views/hr_department.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}