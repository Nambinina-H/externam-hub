export interface ApiError {
  detail: string;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
