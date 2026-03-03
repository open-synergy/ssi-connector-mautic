# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Mautic Connector - Form Webhook Queue",
    "version": "14.0.2.1.0",
    "category": "Connector",
    "author": "PT. Simetri Sinergi Indonesia",
    "website": "https://simetri-sinergi.id",
    "license": "AGPL-3",
    "depends": [
        "ssi_connector_mautic",
        "crm",
        "utm",
        "muk_rest",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "data/muk_restapi_endpoint.xml",
        "views/mautic_webhook_queue_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
