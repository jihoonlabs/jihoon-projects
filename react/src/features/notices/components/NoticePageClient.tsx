'use client'

import { useEffect } from 'react'
import { fetchNotices } from '../api/noticeApi'
import { setNotices } from '../noticeSlice'
import { useAppDispatch, useAppSelector } from '@/store/hooks'

export default function NoticePageClient() {
  // vue: store.action()
  const dispatch = useAppDispatch()
  // vue: const notices = store.notices
  const notices = useAppSelector(state => state.notices.list)

  // useEffect(컴포넌트 마운트시 실행) vue: onMounted(async () => { ... })
  useEffect(() => {
    fetchNotices().then(data => {
      // store.notices = data
      dispatch(setNotices(data))
    })
  }, [dispatch])

  return (
    <main>
      <h1>Notice List</h1>

      {/*
      | v-if / v-else
      */}
      {notices.length === 0 ? (
        <p>No notices found.</p>
      ) : (
        <ul>
          {/*
          | v-for="notice in notices"
          */}
          {notices.map(notice => (
            <li key={notice.id}>
              <h2>{notice.title}</h2>
              <p>{notice.content}</p>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}