# Sourced by the hooks and the updater, from the brain's root.
#
# A brain's GitHub copy is the owner's private repository. It is never BigWork's public kit, the
# place the engine is downloaded from. On 2026-10-07 a rehearsal brain built inside a clone of the
# public kit pushed itself there through its own auto-save. These two guards make that impossible:
# nothing in a brain pushes when "origin" is the kit's home.

aios_kit_home() {
  url=$(git remote get-url origin 2>/dev/null) || return 1
  low=$(printf '%s' "$url" | tr '[:upper:]' '[:lower:]')
  home=$(printf '%s' "${AIOS_REPO:-BigWork-AI/aios-starter}" | tr '[:upper:]' '[:lower:]')
  case "$low" in
    *"$home"|*"$home.git"|*"$home/"|*"$home.git/"|*bigwork-ai/aios-starter|*bigwork-ai/aios-starter.git|*bigwork-ai/aios-starter/|*bigwork-ai/aios-starter.git/) return 0 ;;
  esac
  return 1
}

# aios_push <git push arguments>: pushes, unless origin is the kit's home.
aios_push() {
  if aios_kit_home; then
    echo "This folder's GitHub copy is BigWork's public kit, not your brain. Nothing was pushed. Tell BigWork."
    return 1
  fi
  git push "$@"
}
