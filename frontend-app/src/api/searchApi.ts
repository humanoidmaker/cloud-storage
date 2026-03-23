import client from './client';

export interface SearchParams {
  q: string;
  type?: string;
  date_from?: string;
  date_to?: string;
  tag_id?: string;
  folder_id?: string;
  starred?: boolean;
  sort?: string;
  order?: string;
  page?: number;
  page_size?: number;
}

export const searchApi = {
  search: (params: SearchParams) => client.get('/api/search', { params }),
};
