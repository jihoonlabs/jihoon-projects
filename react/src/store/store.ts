import { configureStore } from '@reduxjs/toolkit';

import noticeReducer from '@/features/notices/noticeSlice';
import postReducer from '@/features/posts/postSlice';

export const store = configureStore({
  reducer: {
    // notices 관련 상태 관리
    notices: noticeReducer,

    // posts 관련 상태 관리
    posts: postReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
