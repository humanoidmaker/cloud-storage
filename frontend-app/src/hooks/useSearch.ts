import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '../api/searchApi';

export function useSearch() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const result = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchApi.search({ q: debouncedQuery }).then((r) => r.data),
    enabled: debouncedQuery.length > 0,
  });

  return { query, setQuery, ...result };
}
