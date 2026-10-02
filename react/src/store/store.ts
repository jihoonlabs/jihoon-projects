import { configureStore } from '@reduxjs/toolkit';

import noticeReducer from '@/features/notices/noticeSlice';
import postReducer from '@/features/posts/postSlice';

export const store = configureStore({
  reducer: {
    notices: noticeReducer,

    posts: postReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
