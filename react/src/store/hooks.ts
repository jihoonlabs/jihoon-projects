import {
  useDispatch,
  useSelector,
  type TypedUseSelectorHook,
} from 'react-redux';
import type { RootState, AppDispatch } from './store';

// dispatch 
export const useAppDispatch: () => AppDispatch = useDispatch;

// state 
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
