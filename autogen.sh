#!/bin/bash
set -e

aclocal $ACINCLUDE
autoconf
python -c "import tools.buildutil; tools.buildutil.create_versions_file('git')"
