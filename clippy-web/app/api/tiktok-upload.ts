import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const response = await fetch(
      'https://open.tiktokapis.com/v2/post/publish/inbox/video/init/',
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${process.env.TIKTOK_ACCESS_TOKEN}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
      }
    )

    const data = await response.json()
    res.status(200).json(data)
  } catch (error) {
    res.status(500).json({ error: 'Failed to upload' })
  }
}
