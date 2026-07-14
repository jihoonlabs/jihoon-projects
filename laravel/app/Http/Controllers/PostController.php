<?php

namespace App\Http\Controllers;

use App\Models\Post;
use Illuminate\Http\Request;

class PostController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index()
    {
        $posts = Post::latest()->get();

        return response()->json([
            'message' => 'Post list',
            'data' => $posts,
        ]);
    }

    /**
     * Show the form for creating a new resource.
     */
    public function create()
    {
        //
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'content' => ['required', 'string'],
            'image_url' => ['nullable', 'string'],
        ]);

        $post = Post::create($validated);

        return response()->json([
            'message' => 'Post created',
            'data' => $post,
        ], 201);
    }

    /**
     * Display the specified resource.
     */
    public function show(Post $post)
    {
        return response()->json([
            'message' => 'Post detail',
            'data' => $post,
        ]);
    }

    /**
     * Show the form for editing the specified resource.
     */
    public function edit(Post $post)
    {
        //
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, Post $post)
    {
        // 수정 요청 데이터 검증
        $validated = $request->validate([
            'content' => ['required', 'string'],
            'image_url' => ['nullable', 'string'],
        ]);

        // Route Model Binding으로 찾은 게시글 수정
        $post->update($validated);

        return response()->json([
            'message' => 'Post updated',
            'data' => $post,
        ]);
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(Post $post)
    {
        // Route Model Binding으로 찾은 게시글 삭제
        $post->delete();

        return response()->json([
            'message' => 'Post deleted',
        ]);
    }
}
