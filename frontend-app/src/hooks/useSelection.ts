import { useState, useCallback } from 'react';

export function useSelection() {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const select = useCallback((id: string, event?: React.MouseEvent) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (event?.ctrlKey || event?.metaKey) {
        if (next.has(id)) next.delete(id);
        else next.add(id);
      } else if (event?.shiftKey) {
        next.add(id);
      } else {
        next.clear();
        next.add(id);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback((ids: string[]) => {
    setSelectedIds(new Set(ids));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const isSelected = useCallback((id: string) => selectedIds.has(id), [selectedIds]);

  return { selectedIds: Array.from(selectedIds), select, selectAll, clearSelection, isSelected, count: selectedIds.size };
}
