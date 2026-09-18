import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const { pathname } = request.nextUrl;

  if (!token && pathname.startsWith('/tickets')) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (token && pathname === '/login') {
    const ticketsUrl = new URL('/tickets', request.url);
    return NextResponse.redirect(ticketsUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/tickets/:path*', '/login'],
};
