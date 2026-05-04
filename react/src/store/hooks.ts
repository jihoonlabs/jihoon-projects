import { useDispatch, useSelector, type TypedUseSelectorHook } from 'react-redux'
import type { RootState, AppDispatch } from './store'

// dispatch 타입 지정
export const useAppDispatch: () => AppDispatch = useDispatch

// state 타입 지정
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector