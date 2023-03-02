# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Non-Profit',
    'version': '0.1',
    'category': 'Non-Profit',
    'description': "Modules for non-profit organization",
    'author': 'Kitti U.',
    'website': 'http://www.ecosoft.co.th',
    'depends': ['account',
                'account_voucher',
                'web_m2x_options',
                ],
    'data': [
        'security/module_data.xml',
        'security/npo_security.xml',
        'security/ir.model.access.csv',
        'views/npo_view.xml',
        'report/cash_register_item_report_view.xml',
        'report/hwf_monthly_report_view.xml',
        'views/account_view.xml',
        'report/hwf_monthly_report_wizard.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
