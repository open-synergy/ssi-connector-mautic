# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Mautic Connector",
    "version": "14.0.1.0.0",
    "category": "Connector",
    "author": "PT. Simetri Sinergi Indonesia",
    "website": "https://simetri-sinergi.id",
    "license": "AGPL-3",
    "depends": [
        "base",
        "queue_job",
        "component",
        "connector",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/mautic_backend_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
