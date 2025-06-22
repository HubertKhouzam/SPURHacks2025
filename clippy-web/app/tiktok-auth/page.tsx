'use client'

import { useEffect, useState } from 'react'

export default function ClippyAIDashboard() {
  const [code, setCode] = useState<string | null>(null)
  const [token, setToken] = useState<any>(null)
  const [videoUrl] = useState('https://clipdaddy.co/video.mp4')

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
      params.append('client_key', 'sbawf7caqj8uuzazw8')
      params.append('client_secret', 'MvMm4uH37w0QKO8gQjs5mQHn8MsXBrX1')
      params.append('code', authCode)
      params.append('grant_type', 'authorization_code')
      params.append(
        'redirect_uri',
        'https://spur-hacks2025.vercel.app/tiktok-auth/'
      )

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
      setToken(data.access_token)
      return data
    } catch (err) {
      console.error('❌ Error fetching access token:', err)
      return null
    }
  }

  const submitVideo = async () => {
    const response = await fetch('/api/tiktok-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        access_token: token, // Your TikTok OAuth access token
        post_info: {
          title: 'this will be a funny #cat video on your @tiktok #fyp',
          privacy_level: 'SELF_ONLY',
          disable_duet: false,
          disable_comment: true,
          disable_stitch: false,
          video_cover_timestamp_ms: 1000,
        },
        source_info: {
          source: 'PULL_FROM_URL',
          video_url: 'https://clipdaddy.co/videoplayback.mp4',
        },
      }),
    })

    const data = await response.json()
    console.log('🎥 TikTok Init Response:', data)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-3xl font-bold text-gray-900">
              Clippy<span className="text-purple-600">AI</span>
            </h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Title Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Generated Clips
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Review and manage your AI-generated short form clips
          </p>
        </div>

        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-2xl shadow-lg p-6 max-w-md">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
              Preview
            </h3>
            <div className="relative">
              <video
                src={videoUrl}
                controls
                className="w-full rounded-lg shadow-md"
                style={{ maxHeight: '400px' }}
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            </div>
            <p className="text-sm text-gray-500 mt-2 text-center">
              Ready to publish to TikTok
            </p>
          </div>
        </div>

        {/* Publish Button */}
        <div className="text-center">
          <button
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-12 py-4 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 hover:from-purple-700 hover:to-blue-700"
            onClick={submitVideo}
          >
            🚀 Publish Clip
          </button>
        </div>
      </div>
    </div>
  )
}
