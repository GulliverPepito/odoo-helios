# -*- coding: utf-8 -*-
###################################################################################
#
#    Intellego-BI.com
#    Copyright (C) 2017-TODAY Intellego Business Intelligence S.A.(<http://www.intellego-bi.com>).
#    Author: Rodolfo Bermúdez Neubauer(<https://www.intellego-bi.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
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
###################################################################################
{
    'name': 'Chile - RRHH Solicitud de Préstamo Empleado',
    'version': '12.0.1.0.0',
    'summary': 'Préstamos al Personal descontados vía Nómina',
    'description': """
        Flujo de trabajo para solicitar, aprobar, desembolsar y pagar préstamos vía nómina.
        """,
    'category': 'Human Resources',
    'author': 'Intellego-BI.com',
    'company': 'Intellego-BI.com',
    'website': 'https://www.Intellego-BI.com',
    'maintainer': 'Intellego-BI.com',
    'depends': [
        'base', 'hr_payroll', 'hr', 'account', 'l10n_cl_hr',
    ],
    'data': [
        'views/hr_chile_menus.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/salary_rule_prestamo.xml',
        'data/hr_prestamo_sequence.xml',
        'views/hr_prestamo.xml',
        'views/hr_prestamo_config.xml',
        'views/hr_prestamo_payroll.xml',
        'views/hr_prestamo_acc.xml',
        'views/hr_prestamo_menu.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
