import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { Post } from './types/post'

interface PostState {
  list: Post[]
}

const initialState: PostState = {
  list: [],
}

const postSlice = createSlice({
  name: 'posts',
  initialState,
  reducers: {
    setPosts(state, action: PayloadAction<Post[]>) {
      state.list = action.payload
    },
  },
})

export const { setPosts } = postSlice.actions

export default postSlice.reducer