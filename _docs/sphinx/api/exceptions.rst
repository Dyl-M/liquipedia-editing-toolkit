Exceptions
==========

Exception hierarchy. All exceptions raised by ``lptk`` inherit from :class:`~lptk.LPTKError`,
allowing a single ``except`` clause to catch any package-specific error.

.. autoexception:: lptk.LPTKError
   :members:
   :show-inheritance:

.. autoexception:: lptk.ConfigurationError
   :members:
   :show-inheritance:

.. autoexception:: lptk.APIError
   :members:
   :show-inheritance:

.. autoexception:: lptk.StartGGAPIError
   :members:
   :show-inheritance:

.. autoexception:: lptk.WikitextParseError
   :members:
   :show-inheritance:
