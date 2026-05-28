Getting Started
===============

Prerequisites
-------------

Your platform of choice will need the following software installed:

* `uv`_ — Python package and project manager. uv will provision the right Python interpreter for you, so a system Python is not required.
* Git.

.. _uv: https://docs.astral.sh/uv/

Installing uv
-------------

On macOS and Linux::

   curl -LsSf https://astral.sh/uv/install.sh | sh

On Windows (PowerShell)::

   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Other installation methods (Homebrew, pipx, standalone binaries) are described in the `uv installation guide`_.

.. _uv installation guide: https://docs.astral.sh/uv/getting-started/installation/

Installation
------------

**Chimera** currently lives on Github_. Clone the repository and let uv handle the environment and dependencies for you:

.. _Github: https://github.com/astroufsc/chimera

::

   git clone https://github.com/astroufsc/chimera.git
   cd chimera
   uv sync

``uv sync`` creates a project-local virtual environment in ``.venv/``, installs Chimera in editable mode, and installs every dependency pinned in ``uv.lock``. The required Python interpreter (3.13 or newer) is downloaded automatically if it is not already available.

Running Chimera
---------------

Once installed, use ``uv run`` to launch the CLI entry points without having to activate the virtual environment::

   uv run chimera -vv

The other entry points work the same way::

   uv run chimera-cam
   uv run chimera-tel
   uv run chimera-dome
   uv run chimera-focus
   uv run chimera-filter
   uv run chimera-rotator
   uv run chimera-sched
   uv run chimera-weather

On the first run, Chimera creates a sample configuration file with fake instruments under ``$HOME/.chimera/chimera.config`` (``%HOMEPATH%\.chimera\chimera.config`` on Windows).

If you prefer the traditional workflow, activate the environment once and then call the scripts directly:

On macOS and Linux::

   source .venv/bin/activate
   chimera -vv

On Windows (PowerShell)::

   .venv\Scripts\Activate.ps1
   chimera -vv

Installing without a clone
--------------------------

To install Chimera into an existing uv-managed project without cloning the repository::

   uv add git+https://github.com/astroufsc/chimera.git

Or, to install it as a standalone tool that exposes the ``chimera`` commands globally::

   uv tool install git+https://github.com/astroufsc/chimera.git

Dependencies
------------

uv resolves and installs the dependencies declared in ``pyproject.toml`` (pinned in ``uv.lock``), including:

* astropy
* msgspec
* numpy
* pyephem
* pynng
* python-dateutil
* PyYAML
* rich
* SQLAlchemy

Development setup
-----------------

To work on Chimera itself, install the ``dev`` and ``docs`` dependency groups as well::

   uv sync --all-groups

Run the test suite with::

   uv run pytest

Build the documentation with::

   uv run --group docs sphinx-build -b html docs docs/_build/html
