import { configureStore } from '@reduxjs/toolkit';
import { render, screen, within } from '@testing-library/react';
import { Provider } from 'react-redux';
import { expect, it, vi } from 'vitest';
import { fetchPosts } from '../../api/postApi';
import postReducer from '../../postSlice';
import type { Post } from '../../types/post';
import PostList from '../PostList';

vi.mock('../../api/postApi', () => ({ fetchPosts: vi.fn() }));

function post(id: number, title: string, imageUrl: string | null): Post {
  return {
    id,
    title,
    content: '投稿本文',
    image_url: imageUrl,
    like_count: 0,
    comment_count: 0,
    created_at: '2026-10-20',
    updated_at: '2026-10-20',
  };
}

it('保存済みの投稿画像は有効なHTTPまたはHTTPSのURLだけを表示する', async () => {
  vi.mocked(fetchPosts).mockResolvedValue([
    post(1, 'HTTPSの画像', 'https://example.com/image.jpg'),
    post(2, 'HTTPの画像', 'http://example.com/image.jpg'),
    post(3, '許可外の画像', 'ftp://example.com/image.jpg'),
    post(4, '相対パスの画像', '/image.jpg'),
    post(5, '不正なURLの画像', 'not a URL'),
    post(6, '画像なし', null),
  ]);
  const store = configureStore({ reducer: { posts: postReducer } });

  render(
    <Provider store={store}>
      <PostList />
    </Provider>,
  );

  await screen.findByRole('heading', { name: '画像なし' });

  const images = within(screen.getByRole('list')).getAllByRole('img');
  expect(images).toHaveLength(2);
  expect(screen.getByRole('img', { name: 'HTTPSの画像' })).toHaveAttribute(
    'src',
    'https://example.com/image.jpg',
  );
  expect(screen.getByRole('img', { name: 'HTTPの画像' })).toHaveAttribute(
    'src',
    'http://example.com/image.jpg',
  );
});
