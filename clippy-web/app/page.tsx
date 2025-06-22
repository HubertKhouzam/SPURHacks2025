'use client'

export default function TikTokLoginPreview() {
  const handleTikTokLogin = () => {
    const CLIENT_KEY = 'sbawf7caqj8uuzazw8'
    const REDIRECT_URI = 'https://spur-hacks2025.vercel.app/tiktok-auth/'

    const url = new URL('https://www.tiktok.com/v2/auth/authorize/')
    url.searchParams.set('client_key', CLIENT_KEY)
    url.searchParams.set('scope', 'user.info.basic')
    url.searchParams.set('response_type', 'code')
    url.searchParams.set('redirect_uri', REDIRECT_URI)
    window.location.href = url.toString() // ✅ actually navigates to TikTok

    console.log('button clicked')
  }

  return (
    <div>
      <button onClick={handleTikTokLogin}>Generate Auth URL</button>
    </div>
  )
}
