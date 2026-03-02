# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MauticBackend(models.Model):
    """Mautic Backend - stores connection parameters to a Mautic instance."""

    _name = "mautic.backend"
    _inherit = "connector.backend"
    _description = "Mautic Backend"

    name = fields.Char(
        string="Name",
        required=True,
    )
    version = fields.Selection(
        selection=[
            ("3", "Mautic 3"),
            ("4", "Mautic 4"),
            ("5", "Mautic 5"),
        ],
        string="Version",
        required=True,
        default="4",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    @api.model
    def _select_versions(self):
        """Available Mautic versions."""
        return [
            ("3", "Mautic 3"),
            ("4", "Mautic 4"),
            ("5", "Mautic 5"),
        ]
