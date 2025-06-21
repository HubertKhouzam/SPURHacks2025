'use client'

import { useState } from 'react'

export default function TikTokLoginPreview() {
  const [authUrl, setAuthUrl] = useState('')

  const handleTikTokLogin = () => {
    const CLIENT_KEY = 'sbawf7caqj8uuzazw8'
    const REDIRECT_URI = 'https://spur-hacks2025.vercel.app/auth/'

    const state = Math.random().toString(36).substring(2)

    const url = new URL('https://www.tiktok.com/v2/auth/authorize/')
    url.searchParams.set('client_key', CLIENT_KEY)
    url.searchParams.set('scope', 'user.info.basic')
    url.searchParams.set('response_type', 'code')
    url.searchParams.set('redirect_uri', REDIRECT_URI)
    url.searchParams.set('state', state)

    setAuthUrl(url.toString())
  }

  return (
    <div>
      <button onClick={handleTikTokLogin}>Generate Auth URL</button>
      {authUrl && (
        <div>
          <p>Auth URL (copy & paste into browser):</p>
          <textarea
            readOnly
            rows={4}
            cols={80}
            value={authUrl}
            style={{ fontFamily: 'monospace' }}
          />
          <br />
          <a href={authUrl} target="_blank" rel="noopener noreferrer">
            Open TikTok Login in New Tab
          </a>
        </div>
      )}
    </div>
  )
}
