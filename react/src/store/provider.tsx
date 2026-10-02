'use client';

import { Provider } from 'react-redux';
import { store } from './store';

export function StoreProvider({ children }: { children: React.ReactNode }) {
  // Redux
  return <Provider store={store}>{children}</Provider>;
}
