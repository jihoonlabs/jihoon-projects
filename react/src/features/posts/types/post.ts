export interface Post {
  id: number
  title: string
  content: string
  image_url: string | null
  like_count: number
  comment_count: number
  created_at: string
  updated_at: string
}