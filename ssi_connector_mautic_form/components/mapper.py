# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""
Mapper: mautic.crm.lead.mapper
================================

Maps a Mautic form submission JSON payload directly to ``crm.lead`` fields.
No ``res.partner`` creation or relation is performed.

Expected payload structure (typical Mautic form submission webhook)::

    {
        "mautic.form_on_submit": [
            {
                "submission": {
                    "id": 123,
                    "form": {"id": 1, "name": "Contact Form"},
                    "results": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                        "phone": "+6281234567890",
                        "company": "Acme Inc",
                        "message": "I want to know more",
                        "utm_campaign": "spring_sale",
                        "utm_medium": "email",
                        "utm_source": "newsletter"
                    }
                }
            }
        ]
    }

The mapper also accepts a flattened format where the keys are at the
top level of the payload dict.
"""

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)

# Fields that are mapped explicitly and should NOT appear in description
_MAPPED_FIELDS = {
    "first_name",
    "firstname",
    "last_name",
    "lastname",
    "email",
    "phone",
    "company",
    "company_name",
    "utm_campaign",
    "utm_medium",
    "utm_source",
    "mautic_id",
    "id",
}


class MauticCrmLeadMapper(Component):
    """Map a Mautic form submission payload to crm.lead fields."""

    _name = "mautic.crm.lead.mapper"
    _inherit = "base.import.mapper"
    _apply_on = ["mautic.crm.lead"]
    _collection = "mautic.backend"
    _usage = "import.mapper"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_results(self, record):
        """Extract the form results dict from the payload.

        Supports both the nested webhook structure and a flat dict.
        """
        # Nested: mautic.form_on_submit[0].submission.results
        submissions = record.get("mautic.form_on_submit", [])
        if submissions and isinstance(submissions, list):
            submission = submissions[0].get("submission", {})
            return submission.get("results", {})
        # Try the submission key directly
        submission = record.get("submission", {})
        if isinstance(submission, dict) and submission.get("results"):
            return submission["results"]
        # Flat dict: keys are directly on the payload
        return record

    # ------------------------------------------------------------------
    # Mappings
    # ------------------------------------------------------------------

    @mapping
    def contact_name(self, record):
        results = self._extract_results(record)
        first = results.get("first_name") or results.get("firstname") or ""
        last = results.get("last_name") or results.get("lastname") or ""
        contact_name = " ".join(part for part in [first, last] if part).strip()
        return {"contact_name": contact_name or "Unknown"}

    @mapping
    def lead_name(self, record):
        results = self._extract_results(record)
        first = results.get("first_name") or results.get("firstname") or ""
        last = results.get("last_name") or results.get("lastname") or ""
        contact_name = " ".join(part for part in [first, last] if part).strip()
        return {"name": "Lead from %s" % (contact_name or "Mautic Form")}

    @mapping
    def email_from(self, record):
        results = self._extract_results(record)
        email = results.get("email") or ""
        return {"email_from": email}

    @mapping
    def phone(self, record):
        results = self._extract_results(record)
        phone = results.get("phone") or ""
        return {"phone": phone}

    @mapping
    def partner_name(self, record):
        """Map company name to partner_name on crm.lead (company field)."""
        results = self._extract_results(record)
        company = results.get("company") or results.get("company_name") or ""
        if company:
            return {"partner_name": company}
        return {}

    @mapping
    def description(self, record):
        """Put remaining (unmapped) form fields into the lead description."""
        results = self._extract_results(record)
        extra_lines = []
        for key, value in results.items():
            if key.lower() not in _MAPPED_FIELDS and value:
                extra_lines.append("%s: %s" % (key, value))
        description = "\n".join(extra_lines) if extra_lines else ""
        return {"description": description}

    @mapping
    def utm_campaign(self, record):
        """Search or create utm.campaign from the payload string."""
        results = self._extract_results(record)
        campaign_name = results.get("utm_campaign") or ""
        if not campaign_name:
            return {}
        campaign = self.env["utm.campaign"].search(
            [("name", "=ilike", campaign_name)], limit=1
        )
        if not campaign:
            campaign = self.env["utm.campaign"].create({"name": campaign_name})
        return {"campaign_id": campaign.id}

    @mapping
    def utm_medium(self, record):
        """Search or create utm.medium from the payload string."""
        results = self._extract_results(record)
        medium_name = results.get("utm_medium") or ""
        if not medium_name:
            return {}
        medium = self.env["utm.medium"].search(
            [("name", "=ilike", medium_name)], limit=1
        )
        if not medium:
            medium = self.env["utm.medium"].create({"name": medium_name})
        return {"medium_id": medium.id}

    @mapping
    def utm_source(self, record):
        """Search or create utm.source from the payload string."""
        results = self._extract_results(record)
        source_name = results.get("utm_source") or ""
        if not source_name:
            return {}
        source = self.env["utm.source"].search(
            [("name", "=ilike", source_name)], limit=1
        )
        if not source:
            source = self.env["utm.source"].create({"name": source_name})
        return {"source_id": source.id}
