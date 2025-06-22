'use client'

import { useEffect, useState } from 'react'

export default function ClippyAIDashboard() {
  const [code, setCode] = useState<string | null>(null)
  const [tokenResponse, setTokenResponse] = useState<any>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    fetchAccessToken(code || '')
  }, [])

  const fetchAccessToken = async (authCode: string) => {
    const CLIENT_KEY = 'sbawf7caqj8uuzazw8'
    const CLIENT_SECRET = 'MvMm4uH37w0QKO8gQjs5mQHn8MsXBrX1'
    const REDIRECT_URI = 'https://spur-hacks2025.vercel.app/tiktok-auth/'

    if (!authCode) {
      console.warn('⚠️ No authorization code provided.')
      return null
    }

    try {
      const body = new URLSearchParams({
        client_key: CLIENT_KEY,
        client_secret: CLIENT_SECRET,
        code: authCode,
        grant_type: 'authorization_code',
        redirect_uri: REDIRECT_URI,
      })

      console.log('📤 Sending Token Request:', body.toString())

      const response = await fetch(
        'https://open.tiktokapis.com/v2/oauth/token/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache',
          },
          body: body.toString(),
        }
      )

      const data = await response.json()
    } catch (err) {
      console.error('❌ Exception during token request:', err)
      return null
    }
  }

  return (
    <div>
      <h1>Clippy AI Dashboard</h1>
      <p>Authorization Code: {code}</p>
      <pre>Access Token Response: {JSON.stringify(tokenResponse, null, 2)}</pre>
    </div>
  )
}
