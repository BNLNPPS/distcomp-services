#!/bin/bash
# Integrity gate for a panda-server upgrade (UPGRADE.md, procedure step 2).
# Installs the target commit into a throwaway virtual environment under the
# production package versions as constraints, then imports every module and
# every configured class. Runs on any host with the production Python.
#
#   run-gate.sh <commit-or-tag> <constraints.txt> <panda_jedi.cfg> <panda_server.cfg> [module:Class ...]
#
# constraints.txt is the production venv's `pip freeze` without the
# panda-server, panda-common and panda-jedi lines; the two configuration
# files are the production ones with the password lines removed. Extra
# module:Class arguments name modules outside panda-server to load, for
# example the ePIC throttler, with their checkout on PYTHONPATH_EXTRA.
set -euo pipefail
TARGET=$1; CONSTRAINTS=$2; JEDI_CFG=$3; SERVER_CFG=$4; shift 4
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${GATE_DIR:-$PWD/gate-$(date +%Y%m%d-%H%M%S)}
PY=${GATE_PYTHON:-python3.11}
mkdir -p "$WORK/log"
$PY -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -q -U pip setuptools wheel
"$WORK/venv/bin/pip" install -c "$CONSTRAINTS" \
    "panda-server[postgres,mcp] @ git+https://github.com/PanDAWMS/panda-server.git@$TARGET" > "$WORK/pip-install.log" 2>&1
"$WORK/venv/bin/pip" check
"$WORK/venv/bin/pip" show panda-server panda-common | grep -E "^(Name|Version)"
# the settings that shape imports, from the shipped templates
cd "$WORK/venv/etc/panda"
for f in panda_server panda_jedi panda_common; do cp -n $f.cfg.rpmnew $f.cfg; done
sed -i -E "s#^(logdir\s*=\s*).*#\1$WORK/log#" panda_common.cfg panda_server.cfg panda_jedi.cfg
sed -i -E 's/^# backend = postgres/backend = postgres/; s/^(schemaPANDA\s*=\s*).*/\1DOMA_PANDA/; s/^(schemaMETA\s*=\s*).*/\1DOMA_PANDAMETA/; s/^(schemaPANDAARCH\s*=\s*).*/\1DOMA_PANDAARCH/; s/^(schemaJEDI\s*=\s*).*/\1DOMA_PANDA/; s/^(schemaDEFT\s*=\s*).*/\1DOMA_DEFT/' panda_server.cfg
cd "$WORK"
SP=$WORK/venv/lib/$PY/site-packages
export PANDA_HOME=$WORK/venv TZ=UTC
export PYTHONPATH=$SP/pandacommon:$SP/pandaserver${PYTHONPATH_EXTRA:+:$PYTHONPATH_EXTRA}
"$WORK/venv/bin/python" "$HERE/import_walk.py" 2>/dev/null | grep -v snakemake | tee "$WORK/import-walk.log"
"$WORK/venv/bin/python" "$HERE/config_load.py" "$JEDI_CFG" "$SERVER_CFG" "$@" 2>/dev/null | grep -v snakemake | tee "$WORK/config-load.log"
