'use client'

/*
| Redux Provider
| Redux store를 React 컴포넌트 트리에 제공
| (Vue의 Pinia 등록과 유사)
*/
import { Provider } from 'react-redux'
import { store } from './store'

export function StoreProvider({ children }: { children: React.ReactNode }) {
  // 이 내부안에서만 Redux 사용 가능
  return <Provider store={store}>{children}</Provider>
}