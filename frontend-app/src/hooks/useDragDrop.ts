import { useState, useCallback } from 'react';

export function useDragDrop(onDrop: (files: File[]) => void) {
  const [isDragging, setIsDragging] = useState(false);
  let dragCounter = 0;

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    dragCounter++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter === 0) setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    dragCounter = 0;
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) onDrop(files);
  }, [onDrop]);

  return { isDragging, handleDragEnter, handleDragLeave, handleDragOver, handleDrop };
}
