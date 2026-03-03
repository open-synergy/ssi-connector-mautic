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
                        "page_url": "https://mautic.example.com/page"
                            "?utm_campaign=spring&utm_medium=email"
                    }
                }
            }
        ]
    }

The mapper also accepts a flattened format where the keys are at the
top level of the payload dict.

UTM values are parsed from the ``page_url`` hidden field which is filled
by a JavaScript snippet injected into the Mautic landing page footer.
The script reads ``window.location.href`` and stores the full URL
(including query string) into the hidden field before the form is
submitted.  The mapper then extracts ``utm_campaign``, ``utm_medium``
and ``utm_source`` from the query string.
"""

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

try:
    from urllib.parse import parse_qs, urlparse
except ImportError:
    from urlparse import parse_qs, urlparse

_logger = logging.getLogger(__name__)

# Fields that are mapped explicitly and should NOT appear in description
_MAPPED_FIELDS = {
    "first_name",
    "firstname",
    "last_name",
    "lastname",
    "email",
    "phone",
    "mobile",
    "complete_name",
    "company",
    "company_name",
    "utm_campaign",
    "utm_medium",
    "utm_source",
    "page_url",
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

    def _parse_utm_from_page_url(self, record):
        """Parse UTM parameters from the ``page_url`` hidden field.

        The hidden field is filled by a JavaScript snippet on the Mautic
        landing page with ``window.location.href``, giving us the full
        URL including UTM query parameters.

        Returns a dict::

            {
                "utm_campaign": "spring_sale",
                "utm_medium": "email",
                "utm_source": "google",
            }
        """
        if hasattr(self, "_utm_from_url"):
            return self._utm_from_url

        results = self._extract_results(record)
        page_url = results.get("page_url") or ""
        self._utm_from_url = {}

        if not page_url or page_url == "{pageurl}":
            return self._utm_from_url

        try:
            # Mautic may HTML-encode ampersands in the stored URL
            page_url = page_url.replace("&amp;", "&").replace("&#38;", "&")
            parsed = urlparse(page_url)
            params = parse_qs(parsed.query)
            self._utm_from_url = {
                "utm_campaign": params.get("utm_campaign", [""])[0],
                "utm_medium": params.get("utm_medium", [""])[0],
                "utm_source": params.get("utm_source", [""])[0],
            }
        except Exception:
            _logger.warning("Failed to parse UTM from page_url: %s", page_url)
        return self._utm_from_url

    def _get_utm_value(self, record, key):
        """Get a UTM value.

        Priority:

        1. Direct form results key (e.g. ``utm_campaign``)
        2. Parsed from ``page_url`` hidden field
        """
        results = self._extract_results(record)
        value = results.get(key) or ""
        if value:
            return value
        return self._parse_utm_from_page_url(record).get(key) or ""

    # ------------------------------------------------------------------
    # Mappings
    # ------------------------------------------------------------------

    @mapping
    def contact_name(self, record):
        results = self._extract_results(record)
        # Prefer complete_name, fallback to first + last
        complete = results.get("complete_name") or ""
        if not complete:
            first = results.get("first_name") or results.get("firstname") or ""
            last = results.get("last_name") or results.get("lastname") or ""
            complete = " ".join(part for part in [first, last] if part).strip()
        return {"contact_name": complete or "Unknown"}

    @mapping
    def lead_name(self, record):
        results = self._extract_results(record)
        complete = results.get("complete_name") or ""
        if not complete:
            first = results.get("first_name") or results.get("firstname") or ""
            last = results.get("last_name") or results.get("lastname") or ""
            complete = " ".join(part for part in [first, last] if part).strip()
        return {"name": "Lead from %s" % (complete or "Mautic Form")}

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
    def mobile(self, record):
        results = self._extract_results(record)
        mobile = results.get("mobile") or ""
        return {"mobile": mobile}

    @mapping
    def partner_name(self, record):
        """Map company name to partner_name on crm.lead (company field)."""
        results = self._extract_results(record)
        company = results.get("company") or results.get("company_name") or ""
        if company:
            return {"partner_name": company}
        return {}

    @mapping
    def partner_id(self, record):
        """Search or create res.partner, identified by mobile and/or email.

        Duplicate prevention logic:

        1. Search by ``mobile`` (exact match) — most unique identifier
        2. Search by ``email`` (case-insensitive) if mobile not found
        3. Search by both ``mobile`` OR ``email`` as fallback
        4. Create new partner if no match found

        The partner is linked to the lead via ``partner_id``.
        """
        results = self._extract_results(record)
        email = results.get("email") or ""
        mobile = results.get("mobile") or ""
        phone = results.get("phone") or ""

        if not email and not mobile:
            return {}

        Partner = self.env["res.partner"]
        partner = Partner

        # 1. Search by mobile (most unique)
        if mobile:
            partner = Partner.search([("mobile", "=", mobile)], limit=1)

        # 2. Fallback: search by email
        if not partner and email:
            partner = Partner.search([("email", "=ilike", email)], limit=1)

        # 3. Create new partner if not found
        if not partner:
            # Build partner name
            complete = results.get("complete_name") or ""
            if not complete:
                first = results.get("first_name") or results.get("firstname") or ""
                last = results.get("last_name") or results.get("lastname") or ""
                complete = " ".join(part for part in [first, last] if part).strip()

            partner_vals = {
                "name": complete or email or mobile,
                "is_company": False,
            }
            if email:
                partner_vals["email"] = email
            if mobile:
                partner_vals["mobile"] = mobile
            if phone:
                partner_vals["phone"] = phone

            # Link to parent company if provided
            company_name = results.get("company") or results.get("company_name") or ""
            if company_name:
                company_partner = Partner.search(
                    [
                        ("name", "=ilike", company_name),
                        ("is_company", "=", True),
                    ],
                    limit=1,
                )
                if not company_partner:
                    company_partner = Partner.create(
                        {
                            "name": company_name,
                            "is_company": True,
                        }
                    )
                partner_vals["parent_id"] = company_partner.id

            partner = Partner.create(partner_vals)
            _logger.info(
                "Created new res.partner id=%s (%s)",
                partner.id,
                partner.name,
            )
        else:
            _logger.info(
                "Found existing res.partner id=%s (%s) " "matched by mobile/email",
                partner.id,
                partner.name,
            )

        return {"partner_id": partner.id}

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
        """Search or create utm.campaign from the payload.

        Reads from form results key ``utm_campaign`` first, then falls
        back to parsing the ``page_url`` hidden field.
        """
        campaign_name = self._get_utm_value(record, "utm_campaign")
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
        """Search or create utm.medium from the payload.

        Reads from form results key ``utm_medium`` first, then falls
        back to parsing the ``page_url`` hidden field.
        """
        medium_name = self._get_utm_value(record, "utm_medium")
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
        """Search or create utm.source from the payload.

        Reads from form results key ``utm_source`` first, then falls
        back to parsing the ``page_url`` hidden field.
        """
        source_name = self._get_utm_value(record, "utm_source")
        if not source_name:
            return {}
        source = self.env["utm.source"].search(
            [("name", "=ilike", source_name)], limit=1
        )
        if not source:
            source = self.env["utm.source"].create({"name": source_name})
        return {"source_id": source.id}
