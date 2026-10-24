#!/usr/bin/env bash
# Machine-wide Lean compile gate.
#
# Lake has no job limit: every `lake build` starts about one compiler per core,
# so several agents building at once oversubscribe CPU and memory (each
# compile can take 1-2 GB). This wrapper makes each compile of a `.lean` file
# wait for one of a fixed number of machine-wide slots. A slot is an flock on
# a file, released automatically when the compiler exits, even if it is killed.
#
# Install (per toolchain, in its bin/ directory):
#   ln lean lean.real                        # keep the real binary
#   cp lean-compile-gate.sh lean.tmp && chmod 755 lean.tmp && mv -f lean.tmp lean
# Remove: mv -f lean.real lean
# Reinstall after the toolchain is reinstalled or updated.
#
# Settings (edit here, or set in the environment):
#   LEAN_GATE_SLOTS     shared slots for all throttled compiles   (default 7)
#   LEAN_GATE_PREFIXES  colon-separated directory prefixes to throttle; compiles
#                       started elsewhere run ungated (default: throttle all)
#   LEAN_GATE_RESERVED  directory prefix (e.g. the main checkout used for
#                       merge checks) that also gets one reserved slot
#   LEAN_GATE_DIR       lock directory (default /run/lean-compile-slots)
real="${BASH_SOURCE[0]%/*}/lean.real"
[ -n "${LEAN_GATE_SLOT:-}" ] && exec "$real" "$@"

slots_shared=${LEAN_GATE_SLOTS:-7}
prefixes=${LEAN_GATE_PREFIXES:-}
reserved=${LEAN_GATE_RESERVED:-}
dir=${LEAN_GATE_DIR:-/run/lean-compile-slots}

in_prefix() {  # $1 = colon-separated prefixes
  local IFS=: p
  for p in $1; do
    [ -n "$p" ] && case "$PWD/" in "${p%/}/"*) return 0 ;; esac
  done
  return 1
}

# Only gate compiles of .lean files; --version, --print-prefix, --server, ... run directly.
haslean=""
for a in "$@"; do case "$a" in *.lean) haslean=1; break ;; esac; done
[ -z "$haslean" ] && exec "$real" "$@"
if [ -n "$prefixes" ] && ! in_prefix "$prefixes:$reserved"; then exec "$real" "$@"; fi

mkdir -p "$dir" 2>/dev/null
slots=$(seq 0 $((slots_shared - 1)))
if [ -n "$reserved" ] && in_prefix "$reserved"; then slots="$slots_shared $slots"; fi

waited=""
while :; do
  for i in $slots; do
    exec {fd}>"$dir/slot$i"
    if flock -n "$fd"; then export LEAN_GATE_SLOT=$i; exec "$real" "$@"; fi
    exec {fd}>&-
  done
  if [ -z "$waited" ]; then
    echo "[lean-compile-gate] waiting for a compile slot ($slots_shared busy machine-wide)" >&2
    waited=1
  fi
  sleep 0.3
done
