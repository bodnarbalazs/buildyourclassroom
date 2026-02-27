type Callback = () => void;

const subscribers = new Set<Callback>();

export function subscribeUnauthorized(cb: Callback): () => void {
  subscribers.add(cb);
  return () => { subscribers.delete(cb); };
}

export function notifyUnauthorized(): void {
  subscribers.forEach((cb) => cb());
}
