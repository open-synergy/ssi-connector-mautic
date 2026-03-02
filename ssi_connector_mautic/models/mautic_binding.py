# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""
Base Binding: mautic.binding
=============================

Abstract binding model for all Mautic resources.  Concrete binding models
(e.g. ``mautic.crm.lead``) must inherit this model and add the
``_inherits`` delegation to the target Odoo model.
"""

from odoo import fields, models


class MauticBinding(models.AbstractModel):
    """Abstract binding between an Odoo record and a Mautic resource."""

    _name = "mautic.binding"
    _inherit = "external.binding"
    _description = "Mautic Binding (abstract)"

    backend_id = fields.Many2one(
        comodel_name="mautic.backend",
        string="Mautic Backend",
        required=True,
        ondelete="restrict",
    )
    mautic_id = fields.Char(
        string="Mautic ID",
    )
    sync_date = fields.Datetime(
        string="Last Synchronization",
    )
