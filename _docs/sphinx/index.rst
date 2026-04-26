liquipedia-editing-toolkit
==========================

**Automate Liquipedia editing from start.gg tournament data.**

``liquipedia-editing-toolkit`` (the ``lptk`` package) is a Python toolkit that pairs a typed
`start.gg <https://start.gg>`_ GraphQL client with wikitext generators that produce
`Liquipedia <https://liquipedia.net/>`_-ready content (TeamCards, TeamParticipants, brackets,
prize pool sections). The current focus is Rocket League competitions, with a roadmap toward
generic esports support.

Built with `requests <https://requests.readthedocs.io/>`_, `pydantic <https://docs.pydantic.dev/>`_,
and `liquipydia <https://github.com/Dyl-M/liquipydia>`_ (for Liquipedia DB API v3 access).

Features
--------

- **Typed start.gg client** — Pydantic-validated responses with bearer-token auth
- **Retries with exponential backoff** — automatic recovery from 429/5xx responses
- **Cascading phase analysis** — collect teams from the most advanced phase backward
- **Smart placement lock-in** — bracket-tier mathematics for ongoing tournaments
- **Liquipedia DB integration** — delegated to the dedicated ``liquipydia`` library
- **Context manager** — clean resource management with the ``with`` statement

Quick example
-------------

.. code-block:: python

   from lptk import StartGGClient

   with StartGGClient() as client:
       event_id, name = client.get_event_id("tournament/rlcs-2026/event/main")
       teams = client.get_event_standings(event_id, top_n=16)
       for team in teams:
           print(f"{team.placement}. {team.team_name}")

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting-started
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/client
   api/models
   api/config
   api/exceptions

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog

Data license
------------

Data returned by the start.gg and Liquipedia APIs is subject to the respective platform terms.

- **start.gg:** see the
  `start.gg APIs Terms of Use <https://www.start.gg/about/apitos>`_.
- **Liquipedia:** data returned by the Liquipedia API is subject to
  `CC-BY-SA 3.0 <https://creativecommons.org/licenses/by-sa/3.0/>`_ as required by Liquipedia's
  `API Terms of Use <https://liquipedia.net/api-terms-of-use>`_.
