# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""
Mautic Binder
=============

Base binder for all Mautic binding models.  Concrete binders should
inherit this class and set ``_apply_on``.
"""

from odoo.addons.component.core import AbstractComponent


class MauticBinder(AbstractComponent):
    """Base binder for Mautic connector."""

    _name = "mautic.binder"
    _inherit = "base.binder"
    _collection = "mautic.backend"

    _external_field = "mautic_id"
    _backend_field = "backend_id"
    _odoo_field = "odoo_id"
    _sync_date_field = "sync_date"
