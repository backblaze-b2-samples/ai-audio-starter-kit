import * as React from "react"

const MOBILE_BREAKPOINT = 768
const MOBILE_MEDIA_QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`

function getSnapshot() {
  return window.matchMedia(MOBILE_MEDIA_QUERY).matches
}

function getServerSnapshot() {
  return false
}

function subscribe(onStoreChange: () => void) {
  const mql = window.matchMedia(MOBILE_MEDIA_QUERY)
  mql.addEventListener("change", onStoreChange)

  return () => mql.removeEventListener("change", onStoreChange)
}

export function useIsMobile() {
  return React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
