# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""
Importer: mautic.importer
===========================

Custom importer for Mautic form submissions.  Looks up an existing
``mautic.crm.lead`` binding via the Binder using ``mautic_id``.
If no binding exists, creates a new one (and the underlying ``crm.lead``
via ``_inherits``).  If a binding already exists, updates it.

Returns the ``crm.lead`` ID on success so the caller
(``mautic.webhook.queue._run_import``) can write it back.
"""

import logging

from odoo import fields

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MauticImporter(Component):
    """Import a Mautic form submission into mautic.crm.lead."""

    _name = "mautic.importer"
    _inherit = "base.importer"
    _apply_on = ["mautic.crm.lead"]
    _collection = "mautic.backend"
    _usage = "record.importer"

    def run(self, mautic_id, payload, queue_record=None):
        """Execute the import flow.

        :param mautic_id: external Mautic ID (string)
        :param payload: parsed JSON dict from the Mautic webhook
        :param queue_record: optional ``mautic.webhook.queue`` recordset
        :returns: ID of the ``crm.lead`` record (int)
        """
        binder = self.component(usage="binder")
        mapper = self.component(usage="import.mapper")

        # Look up existing binding
        binding = binder.to_internal(mautic_id)

        # Map the payload to crm.lead values
        map_record = mapper.map_record(payload)

        if binding:
            # ---- UPDATE existing binding / lead ----
            vals = map_record.values()
            _logger.info(
                "Updating mautic.crm.lead binding id=%s (mautic_id=%s) "
                "with values: %s",
                binding.id,
                mautic_id,
                vals,
            )
            binding.write(vals)
            binding.write(
                {
                    "sync_date": fields.Datetime.now(),
                }
            )
            lead_id = binding.odoo_id.id
        else:
            # ---- CREATE new binding + lead ----
            vals = map_record.values(for_create=True)
            vals.update(
                {
                    "backend_id": self.backend_record.id,
                    "mautic_id": str(mautic_id),
                    "sync_date": fields.Datetime.now(),
                }
            )
            _logger.info(
                "Creating new mautic.crm.lead binding "
                "(mautic_id=%s) with values: %s",
                mautic_id,
                vals,
            )
            binding = self.model.create(vals)
            # Bind the external ID via the binder
            binder.bind(mautic_id, binding)
            lead_id = binding.odoo_id.id

        _logger.info(
            "Import completed: mautic_id=%s -> crm.lead id=%s",
            mautic_id,
            lead_id,
        )
        return lead_id
