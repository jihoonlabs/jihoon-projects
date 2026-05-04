import { apiClient } from '@/lib/axios'
import type { Notice } from '../types/notice'

interface NoticeListResponse {
  message: string
  data: Notice[]
}

export const fetchNotices = async (): Promise<Notice[]> => {
  const response = await apiClient.get<NoticeListResponse>('/notices')

  return response.data.data
}