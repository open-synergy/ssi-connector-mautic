import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-open-synergy-ssi-connector-mautic",
    description="Meta package for open-synergy-ssi-connector-mautic Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-ssi_connector_mautic',
        'odoo14-addon-ssi_connector_mautic_form',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
