// Redux store를 React 컴포넌트 트리에 inject하는 역할(뷰의 Pinia 등록)
import PostPageClient from '@/features/posts/components/PostPageClient';
import { StoreProvider } from '@/store/provider';

export default function PostsPage() {
  return (
    // Provider로 감싼 하위에서만 Redux 사용 가능
    <StoreProvider>
      <PostPageClient />
    </StoreProvider>
  );
}
