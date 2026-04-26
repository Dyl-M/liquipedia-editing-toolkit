Client
======

The :class:`~lptk.StartGGClient` is the primary entry point for fetching data from the start.gg
GraphQL API. It handles authentication, rate limiting and exponential-backoff retries on transient
failures.

.. autoclass:: lptk.StartGGClient
   :members:
   :inherited-members:
   :show-inheritance:
