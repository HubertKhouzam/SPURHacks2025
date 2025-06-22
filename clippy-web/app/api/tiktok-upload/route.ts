import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const { access_token, source_info } = await req.json()

    const response = await fetch(
      'https://open.tiktokapis.com/v2/post/publish/video/init/',
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${access_token}`, // Use token from request
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_info: {
            title: 'this will be a funny #cat video on your @tiktok #fyp',
            privacy_level: 'SELF_ONLY',
            disable_duet: false,
            disable_comment: true,
            disable_stitch: false,
            video_cover_timestamp_ms: 1000,
          },
          source_info: {
            source: 'FILE_UPLOAD',
          },
        }),
      }
    )

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Failed to upload' }, { status: 500 })
  }
}
