'use client'

export default function ClippyAIDashboard() {
  const code = new URLSearchParams(window.location.search).get('code')

  const getAccessToken = async () => {
    try {
      const params = new URLSearchParams()
      params.append('client_key', 'sbawf7caqj8uuzazw8')
      params.append('client_secret', 'TV6Nt8GUQ6HDuV9c31c71OpYKmRSwdFs')
      params.append('code', 'CODE') // Replace with real auth code
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
      console.log('Result of code is', code)
      console.log('Data of access token retrieval', data)
      return data // return full object: includes access_token, refresh_token, open_id, etc.
    } catch (err) {
      console.error('Error fetching access token:', err)
      return null
    }
  }

  const submitVideo = async () => {
    const tokenResponse = await getAccessToken()

    if (!tokenResponse || !tokenResponse.access_token) {
      console.error('No access token received.')
      return
    }

    const accessToken = tokenResponse.access_token
    const FILE_UPLOAD = 'clippy-web/public/vid.mov'

    const payload = {
      post_info: {
        title: 'Video of Hubert being freaky #fyp',
        privacy_level: 'SELF_ONLY',
        disable_duet: false,
        disable_comment: false,
        disable_stitch: false,
        video_cover_timestamp_ms: 1000,
      },
      source_info: {
        source: FILE_UPLOAD,
      },
    }

    try {
      const res = await fetch(
        'https://open.tiktokapis.com/v2/post/publish/video/init/',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json; charset=UTF-8',
          },
          body: JSON.stringify(payload),
        }
      )

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.message || 'Failed to initiate upload')
      }

      console.log('Init Success:', data)

      // Continue with chunk upload using data.upload_id
    } catch (err) {
      console.error('Init error:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <button className="text-black " onClick={getAccessToken}>
        {' '}
        Get Access Token
      </button>
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">
              Clippy<span className="text-purple-600">AI</span>
            </h1>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Clips Grid */}
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Generated Clips
          </h2>
          <p className="text-gray-600">
            Review and manage your AI-generated short form clips
          </p>
        </div>
      </div>
      <button
        className="px-8 py-3 text-black hover:pointer flex items-center justify-center border-2 border-solid border-black"
        onClick={submitVideo}
      >
        Publish Clip
      </button>
    </div>
  )
}
