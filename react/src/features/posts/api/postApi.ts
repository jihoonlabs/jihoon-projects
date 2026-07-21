import { apiClient } from '@/lib/axios'
import type { Post } from '../types/post'

// Laravel 게시글 목록 API의 응답 형태
interface PostListResponse {
  message: string
  data: Post[]
}

// 게시글 목록 조회
export async function fetchPosts(): Promise<Post[]> {
  const { data } = await apiClient.get<PostListResponse>('/posts')

  return data.data
}