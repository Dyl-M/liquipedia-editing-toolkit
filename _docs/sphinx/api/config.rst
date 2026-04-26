Configuration
=============

Settings are loaded from environment variables (``LPTK_`` prefix) and credentials from a JSON keys
file (``.tokens/local_keys.json`` by default).

.. autoclass:: lptk.Settings
   :members:
   :show-inheritance:

.. autofunction:: lptk.get_settings

.. autofunction:: lptk.get_token

.. autofunction:: lptk.get_lpdb_token
