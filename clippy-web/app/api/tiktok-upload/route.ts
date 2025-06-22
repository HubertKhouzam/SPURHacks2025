import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const { access_token, source_info } = await req.json()

    const response = await fetch(
      'https://open.tiktokapis.com/v2/post/publish/inbox/video/init/',
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${access_token}`, // Use token from request
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source_info }),
      }
    )

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Failed to upload' }, { status: 500 })
  }
}
