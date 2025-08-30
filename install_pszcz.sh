#!/usr/bin/env bash
set -Eeuo pipefail

# ==== Konfigurace (lze přepsat proměnnými prostředí) ====
REPO_URL="${REPO_URL:-https://github.com/procmadatelzobak/pszcz-flow-simulator}"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/pszcz}"
REPO_DIR="${REPO_DIR:-$INSTALL_ROOT/repo}"
SERVER_ENTRY="${SERVER_ENTRY:-server/net.py}"   # lze změnit např. na "server/app.py" nebo "python -m server.net"
CLIENT_ENTRY="${CLIENT_ENTRY:-client/net.py}"
PY_MIN_MAJOR=3
PY_MIN_MINOR=10

log(){ printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn(){ printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err(){ printf "\033[1;31m[ERR ]\033[0m %s\n" "$*"; }
trap 'err "Selhalo na řádku $LINENO"; exit 1' ERR

# Root/sudo
if [[ "$EUID" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

export DEBIAN_FRONTEND=noninteractive
log "Apt update…"
apt-get update -y
log "Instaluji závislosti…"
apt-get install -y --no-install-recommends \
  ca-certificates curl git build-essential pkg-config \
  python3 python3-venv python3-pip python3-dev \
  libffi-dev libssl-dev libbz2-dev libreadline-dev libsqlite3-dev \
  unzip jq

# Kontrola Pythonu
PYV=$(python3 - <<'PY'
import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)
PY_MAJOR=${PYV%%.*}; PY_MINOR=${PYV#*.}
if (( PY_MAJOR < PY_MIN_MAJOR )) || { (( PY_MAJOR == PY_MIN_MAJOR )) && (( PY_MINOR < PY_MIN_MINOR )); }; then
  err "Potřebuji Python >= ${PY_MIN_MAJOR}.${PY_MIN_MINOR}, nalezeno ${PYV}"
fi
log "Python OK: $PYV"

# Adresáře
mkdir -p "$INSTALL_ROOT"
cd "$INSTALL_ROOT"

# Stažení/aktualizace repa
if [[ -d "$REPO_DIR/.git" ]]; then
  log "Repo existuje, aktualizuji…"
  git -C "$REPO_DIR" fetch --all --prune
  git -C "$REPO_DIR" reset --hard origin/HEAD
else
  log "Klonuji $REPO_URL → $REPO_DIR"
  git clone --depth 1 "$REPO_URL" "$REPO_DIR"
fi

# Setup venvů
setup_venv() {
  local name="$1" subdir="$2"
  local venv="$INSTALL_ROOT/$name/venv"
  mkdir -p "$(dirname "$venv")"
  if [[ ! -d "$venv" ]]; then
    log "Vytvářím venv: $venv"
    python3 -m venv "$venv"
  else
    log "Venv $name už existuje (OK)."
  fi
  source "$venv/bin/activate"
  python -m pip install --upgrade pip wheel setuptools
  local req=""
  if [[ -f "$REPO_DIR/$subdir/requirements.txt" ]]; then
    req="$REPO_DIR/$subdir/requirements.txt"
  elif [[ -f "$REPO_DIR/requirements.txt" ]]; then
    req="$REPO_DIR/requirements.txt"
  fi
  if [[ -n "$req" ]]; then
    log "Instaluji Python závislosti pro $name z $req"
    pip install -r "$req"
  else
    warn "Nenašel jsem requirements pro $name"
  fi
  deactivate
}

setup_venv "server" "server"
setup_venv "client" "client"

# Helper: vytvoří spouštěcí skript
make_runner() {
  local out="$1" venv="$2" entry="$3" wd="$4"
  cat >"$out"<<BASH
#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_ROOT="\${INSTALL_ROOT:-$INSTALL_ROOT}"
REPO_DIR="\${REPO_DIR:-$REPO_DIR}"
ENTRY="\${ENTRY:-$entry}"
cd "$wd"
source "$venv/bin/activate"

# ENTRY může být cesta k .py souboru nebo "python -m modul"
if [[ "\$ENTRY" == *.py ]]; then
  exec python "\$REPO_DIR/\$ENTRY" "\$@"
else
  exec \$ENTRY "\$@"
fi
BASH
  chmod +x "$out"
}

# Start/stop skripty (bez systemd)
make_runner "/usr/local/bin/pszcz-server-start" "$INSTALL_ROOT/server/venv" "$SERVER_ENTRY" "$REPO_DIR"
make_runner "/usr/local/bin/pszcz-client-start" "$INSTALL_ROOT/client/venv" "$CLIENT_ENTRY" "$REPO_DIR"

cat >/usr/local/bin/pszcz-server-stop <<'BASH'
#!/usr/bin/env bash
set -Eeuo pipefail
pkill -f "server/net.py" 2>/dev/null || true
pkill -f "python -m server.net" 2>/dev/null || true
echo "Server zastaven (pokud běžel)."
BASH
chmod +x /usr/local/bin/pszcz-server-stop

cat >/usr/local/bin/pszcz-client-stop <<'BASH'
#!/usr/bin/env bash
set -Eeuo pipefail
pkill -f "client/net.py" 2>/dev/null || true
pkill -f "python -m client.net" 2>/dev/null || true
echo "Klient zastaven (pokud běžel)."
BASH
chmod +x /usr/local/bin/pszcz-client-stop

# Update skript
cat >/usr/local/bin/pszcz-update <<'BASH'
#!/usr/bin/env bash
set -Eeuo pipefail
REPO_DIR="${REPO_DIR:-/opt/pszcz/repo}"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/pszcz}"
log(){ printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
err(){ printf "\033[1;31m[ERR ]\033[0m %s\n" "$*"; }
trap 'err "Update selhal na řádku $LINENO"; exit 1' ERR
if [[ "$EUID" -ne 0 ]]; then exec sudo -E bash "$0" "$@"; fi

log "Aktualizuji repo…"
git -C "$REPO_DIR" fetch --all --prune
git -C "$REPO_DIR" reset --hard origin/HEAD

# Znovu nainstaluj závislosti pro oba venvy (idempotentní)
for pair in "server:server" "client:client"; do
  name="${pair%%:*}"
  sub="${pair##*:}"
  venv="$INSTALL_ROOT/$name/venv"
  if [[ -d "$venv" ]]; then
    source "$venv/bin/activate"
    python -m pip install --upgrade pip wheel setuptools
    req=""
    if [[ -f "$REPO_DIR/$sub/requirements.txt" ]]; then
      req="$REPO_DIR/$sub/requirements.txt"
    elif [[ -f "$REPO_DIR/requirements.txt" ]]; then
      req="$REPO_DIR/requirements.txt"
    fi
    if [[ -n "$req" ]]; then
      log "pip install -r $req"
      pip install -r "$req"
    fi
    deactivate
  fi
 done
log "Hotovo."
BASH
chmod +x /usr/local/bin/pszcz-update

log "Instalace dokončena.
Spuštění serveru: pszcz-server-start
Zastavení serveru: pszcz-server-stop
Spuštění klienta: pszcz-client-start
Zastavení klienta: pszcz-client-stop
Aktualizace kódu: pszcz-update
"
