'use client'
import { useEffect, useState } from 'react'

export default function TikTokLoginPreview() {
  const [isVisible, setIsVisible] = useState(false)

  const handleTikTokLogin = () => {
    const CLIENT_KEY = 'sbawf7caqj8uuzazw8'
    const REDIRECT_URI = 'https://spur-hacks2025.vercel.app/tiktok-auth/'

    const url = new URL('https://www.tiktok.com/v2/auth/authorize/')
    url.searchParams.set('client_key', 'sbawf7caqj8uuzazw8')
    url.searchParams.set('scope', 'user.info.basic')
    url.searchParams.set('response_type', 'code')
    url.searchParams.set('redirect_uri', REDIRECT_URI)
    window.location.href = url.toString() // ✅ actually navigates to TikTok

    console.log('button clicked')
  }

  return (
    <div className="min-h-screen bg-white relative overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-100 via-blue-50 to-indigo-100"></div>
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `radial-gradient(circle at 25% 25%, #6366f1 1px, transparent 1px),
                             radial-gradient(circle at 75% 75%, #8b5cf6 1px, transparent 1px)`,
            backgroundSize: '60px 60px',
          }}
        ></div>
      </div>

      <div className="relative z-10 flex items-center justify-center min-h-screen px-4">
        <div className="max-w-4xl mx-auto text-center">
          {/* Logo */}
          <div
            className={`transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
          >
            <h1 className="text-6xl md:text-7xl font-black text-gray-900 mb-6">
              Clippy
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                AI
              </span>
            </h1>
          </div>

          {/* Tagline */}
          <div
            className={`transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
          >
            <p className="text-xl md:text-2xl text-gray-700 mb-12 max-w-3xl mx-auto leading-relaxed font-light">
              Transform your live streams into viral clips instantly. AI-powered
              face recognition, chat spikes, and voice detection create perfect
              moments while you stream.
            </p>
          </div>

          {/* Features */}
          <div
            className={`transition-all duration-1000 delay-400 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
          >
            <div className="flex flex-wrap justify-center gap-8 mb-16">
              <div className="flex items-center space-x-3 bg-gray-50 px-6 py-3 rounded-full border border-gray-200 hover:shadow-lg transition-all duration-300 hover:scale-105">
                <div className="w-3 h-3 bg-gradient-to-r from-green-400 to-blue-500 rounded-full animate-pulse"></div>
                <span className="text-gray-700 font-medium">
                  Face Recognition
                </span>
              </div>
              <div className="flex items-center space-x-3 bg-gray-50 px-6 py-3 rounded-full border border-gray-200 hover:shadow-lg transition-all duration-300 hover:scale-105">
                <div className="w-3 h-3 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full animate-pulse"></div>
                <span className="text-gray-700 font-medium">Chat Spikes</span>
              </div>
              <div className="flex items-center space-x-3 bg-gray-50 px-6 py-3 rounded-full border border-gray-200 hover:shadow-lg transition-all duration-300 hover:scale-105">
                <div className="w-3 h-3 bg-gradient-to-r from-indigo-400 to-purple-500 rounded-full animate-pulse"></div>
                <span className="text-gray-700 font-medium">
                  Voice Detection
                </span>
              </div>
            </div>
          </div>

          {/* CTA Button */}
          <div
            className={`transition-all duration-1000 delay-600 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
          >
            <button
              onClick={handleTikTokLogin}
              className="group relative px-12 py-4 bg-black text-white font-semibold text-lg rounded-full 
                         hover:bg-gray-800 transition-all duration-300 transform hover:scale-105 
                         hover:shadow-2xl focus:outline-none focus:ring-4 focus:ring-gray-300"
            >
              <span className="relative z-10">Log into TikTok</span>
              <div
                className="absolute inset-0 bg-gradient-to-r from-pink-500 to-purple-600 rounded-full opacity-0 
                              group-hover:opacity-100 transition-opacity duration-300 blur-sm"
              ></div>
            </button>
          </div>

          {/* Subtitle */}
          <div
            className={`transition-all duration-1000 delay-800 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
          >
            <p className="text-gray-500 mt-8 text-sm">
              Bring more viewers to your live streams with instant viral content
            </p>
          </div>
        </div>
      </div>

      {/* Bottom gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-50 to-transparent opacity-50"></div>
    </div>
  )
}
