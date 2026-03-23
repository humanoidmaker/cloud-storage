import { useState, useCallback } from 'react';

interface ContextMenuState {
  x: number;
  y: number;
  isOpen: boolean;
}

export function useContextMenu() {
  const [state, setState] = useState<ContextMenuState>({ x: 0, y: 0, isOpen: false });

  const open = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setState({ x: e.clientX, y: e.clientY, isOpen: true });
  }, []);

  const close = useCallback(() => {
    setState((s) => ({ ...s, isOpen: false }));
  }, []);

  return { ...state, open, close };
}
