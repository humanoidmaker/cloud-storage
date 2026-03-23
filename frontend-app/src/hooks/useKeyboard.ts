import { useEffect } from 'react';

type KeyHandler = (e: KeyboardEvent) => void;

const shortcuts: Record<string, KeyHandler> = {};

export function useKeyboard(key: string, handler: KeyHandler, deps: unknown[] = []) {
  useEffect(() => {
    const listener = (e: KeyboardEvent) => {
      const combo = [e.ctrlKey && 'ctrl', e.shiftKey && 'shift', e.altKey && 'alt', e.key.toLowerCase()]
        .filter(Boolean)
        .join('+');
      if (combo === key.toLowerCase()) {
        e.preventDefault();
        handler(e);
      }
    };
    window.addEventListener('keydown', listener);
    return () => window.removeEventListener('keydown', listener);
  }, [key, handler, ...deps]);
}
