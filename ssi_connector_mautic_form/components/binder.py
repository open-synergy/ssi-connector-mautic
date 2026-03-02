# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""
Binder: mautic.crm.lead
=========================

Resolves Odoo <-> Mautic ID pairs for the CRM lead binding model.
"""

from odoo.addons.component.core import Component


class MauticCrmLeadBinder(Component):
    """Binder for mautic.crm.lead."""

    _name = "mautic.crm.lead.binder"
    _inherit = "mautic.binder"
    _apply_on = ["mautic.crm.lead"]
