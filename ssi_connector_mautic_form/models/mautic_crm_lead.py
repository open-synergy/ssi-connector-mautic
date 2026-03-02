# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""
Binding model: mautic.crm.lead
================================

Binding between an Odoo ``crm.lead`` and a Mautic form submission.
Uses ``_inherits`` delegation so each binding record wraps a real
``crm.lead`` record via ``odoo_id``.
"""

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MauticCrmLead(models.Model):
    """Binding between an Odoo crm.lead and a Mautic form submission."""

    _name = "mautic.crm.lead"
    _inherit = "mautic.binding"
    _inherits = {"crm.lead": "odoo_id"}
    _description = "Mautic CRM Lead Binding"
    _rec_name = "name"

    _sql_constraints = [
        (
            "mautic_lead_uniq",
            "unique(backend_id, mautic_id)",
            "A Mautic binding already exists for this lead and backend.",
        ),
    ]

    odoo_id = fields.Many2one(
        comodel_name="crm.lead",
        string="CRM Lead",
        required=True,
        ondelete="cascade",
    )
