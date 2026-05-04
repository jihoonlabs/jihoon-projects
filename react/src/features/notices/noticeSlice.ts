import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { Notice } from './types/notice'

interface NoticeState {
  list: Notice[]
}

const initialState: NoticeState = {
  list: [],
}

// notices 관련 상태(state)와 상태 변경 로직(reducer)을 정의
// Redux Toolkit를 사용
const noticeSlice = createSlice({
  name: 'notices',
  initialState,
  reducers: {
    setNotices(state, action: PayloadAction<Notice[]>) {
      state.list = action.payload
    },
  },
})

// 컴포넌트에서 dispatch로 호출할 액션 함수
export const { setNotices } = noticeSlice.actions

// store에 등록할 reducer
export default noticeSlice.reducer