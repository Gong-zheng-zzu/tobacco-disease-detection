export function notify(message, type = 'error') {
  window.dispatchEvent(new CustomEvent('app-notify', { detail: { message: String(message), type } }));
}
