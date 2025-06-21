'use client'

import { useEffect, useState } from 'react'

export default function ClippyAIDashboard() {
  const [code, setCode] = useState<string | null>(null)
  const [tokenResponse, setTokenResponse] = useState<any>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    // Log all params nicely
    console.log('URL Params:', Array.from(params.entries()))

    const code = params.get('code')
    const error = params.get('error')
    const state = params.get('state')

    if (error) {
      console.error('❌ TikTok Login Error:', error)
    } else if (code) {
      console.log('✅ TikTok Authorization Code:', code)
      setCode(code)
      // Immediately fetch access token and log the response
      fetchAccessToken(code)
    } else {
      console.warn('⚠️ No code or error in URL.')
    }
  }, [])

  const fetchAccessToken = async (authCode: string) => {
    try {
      const params = new URLSearchParams()
      params.append('client_key', 'YOUR_CLIENT_KEY')
      params.append('client_secret', 'YOUR_CLIENT_SECRET')
      params.append('code', authCode)
      params.append('grant_type', 'authorization_code')
      params.append('redirect_uri', 'https://spur-hacks2025.vercel.app/auth')

      const response = await fetch(
        'https://open.tiktokapis.com/v2/oauth/token/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache',
          },
          body: params.toString(),
        }
      )

      const data = await response.json()
      console.log('✅ Access Token Response:', data)
      setTokenResponse(data)
      return data
    } catch (err) {
      console.error('❌ Error fetching access token:', err)
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
