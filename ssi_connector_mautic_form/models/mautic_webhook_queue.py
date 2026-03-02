# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""
Staging / Queue Model: mautic.webhook.queue
=============================================

Stores raw webhook payloads received from Mautic via the MUK REST API
endpoint.  Records are processed asynchronously: the JSON payload is
parsed, and a connector import job is queued to create or update a
``crm.lead`` via the OCA connector framework.
"""

import json
import logging
import traceback

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MauticWebhookQueue(models.Model):
    """Staging table for Mautic webhook payloads."""

    _name = "mautic.webhook.queue"
    _description = "Mautic Webhook Queue"
    _order = "create_date desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )
    payload_data = fields.Text(
        string="Payload Data",
        help="Raw JSON payload received from Mautic webhook.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        string="State",
        default="draft",
        required=True,
        readonly=True,
        copy=False,
    )
    backend_id = fields.Many2one(
        comodel_name="mautic.backend",
        string="Mautic Backend",
    )
    error_log = fields.Text(
        string="Error Log",
        readonly=True,
        copy=False,
    )
    lead_id = fields.Many2one(
        comodel_name="crm.lead",
        string="CRM Lead",
        readonly=True,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Sequence
    # ------------------------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("mautic.webhook.queue") or "New"
            )
        return super().create(vals)

    def _get_default_backend(self):
        """Return the first active Mautic backend."""
        return self.env["mautic.backend"].search([("active", "=", True)], limit=1)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def action_process_queue(self):
        """Parse JSON payload and queue the connector import job.

        This method can be called from:
        - The "Process" button on the form view
        - The scheduled cron job
        """
        for record in self:
            if record.state != "draft":
                continue
            try:
                payload = json.loads(record.payload_data or "{}")
                mautic_id = str(
                    payload.get("mautic_id")
                    or payload.get("submission", {}).get("id")
                    or payload.get("id")
                    or record.id
                )

                backend = record.backend_id or self._get_default_backend()
                if not backend:
                    raise ValueError(
                        "No active Mautic backend found. "
                        "Please configure at least one backend."
                    )

                # Queue the import job via queue_job
                record.with_delay()._run_import(
                    backend_id=backend.id,
                    mautic_id=mautic_id,
                    payload=payload,
                )

            except Exception as exc:
                _logger.exception(
                    "Error processing webhook queue record %s: %s",
                    record.name,
                    exc,
                )
                record.write(
                    {
                        "state": "error",
                        "error_log": traceback.format_exc(),
                    }
                )

    def _run_import(self, backend_id, mautic_id, payload):
        """Execute the connector import within a queue job context.

        :param backend_id: ID of the ``mautic.backend`` record
        :param mautic_id: external Mautic ID (string)
        :param payload: parsed JSON dict from the webhook
        """
        self.ensure_one()
        try:
            backend = self.env["mautic.backend"].browse(backend_id)
            with backend.work_on("mautic.crm.lead") as work:
                importer = work.component(usage="record.importer")
                lead_id = importer.run(
                    mautic_id=mautic_id,
                    payload=payload,
                    queue_record=self,
                )
            self.write(
                {
                    "state": "done",
                    "lead_id": lead_id,
                    "error_log": False,
                }
            )
        except Exception as exc:
            _logger.exception(
                "Import failed for webhook queue record %s: %s",
                self.name,
                exc,
            )
            self.write(
                {
                    "state": "error",
                    "error_log": traceback.format_exc(),
                }
            )

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------

    @api.model
    def cron_process_queue(self):
        """Scheduled action: process all draft queue records."""
        records = self.search([("state", "=", "draft")])
        _logger.info("Cron: processing %d draft webhook queue records.", len(records))
        records.action_process_queue()
