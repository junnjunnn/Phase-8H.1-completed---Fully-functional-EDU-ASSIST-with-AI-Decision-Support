const referenceEventTarget = new EventTarget()

export const REFERENCE_EVENTS = {
  SUBJECTS_UPDATED: 'subjects:updated',
}

export function notifySubjectsUpdated() {
  referenceEventTarget.dispatchEvent(new Event(REFERENCE_EVENTS.SUBJECTS_UPDATED))
}

export function subscribeSubjectsUpdated(listener) {
  referenceEventTarget.addEventListener(REFERENCE_EVENTS.SUBJECTS_UPDATED, listener)
}

export function unsubscribeSubjectsUpdated(listener) {
  referenceEventTarget.removeEventListener(REFERENCE_EVENTS.SUBJECTS_UPDATED, listener)
}
