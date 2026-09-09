/* eslint-disable @next/next/no-img-element */
'use client'

import { useEffect } from 'react'
import { fetchPosts } from '../api/postApi'
import { setPosts } from '../postSlice'
import { useAppDispatch, useAppSelector } from '@/store/hooks'

export default function PostList() {
  // Redux에 action을 전달하기 위한 dispatch
  const dispatch = useAppDispatch()

  // Redux posts 상태에서 게시글 목록을 가져옴
  const posts = useAppSelector(state => state.posts.list)

  useEffect(() => {
    // 컴포넌트가 처음 렌더링될 때 게시글 목록 API 호출
    fetchPosts()
      .then(data => {
        // API에서 받은 게시글 목록을 Redux에 저장
        dispatch(setPosts(data))
      })
      .catch(error => {
        console.error('Failed to fetch posts:', error)
      })
  }, [dispatch])

  // 게시글이 없을 때 표시
  if (posts.length === 0) {
    return <p>No posts found.</p>
  }

  return (
    <section>
      <ul>
        {posts.map(post => (
          <li key={post.id}>
            <article>
              <h2>{post.title}</h2>

              <p>{post.content}</p>

              {post.image_url && (
                <img
                  src={post.image_url}
                  alt={post.title}
                />
              )}

              <div>
                <span>Likes: {post.like_count}</span>
                <span>Comments: {post.comment_count}</span>
              </div>

              <time>{post.createdAt}</time>
            </article>
          </li>
        ))}
      </ul>
    </section>
  )
}