'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { handleUserLogIn } from '@/app/firebase/auth-service'

export default function ClippyAILogin() {
  const [isVisible, setIsVisible] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  useEffect(() => {
    setIsVisible(true)
  }, [])

  const handleLogin = async () => {
    setIsLoading(true)
    setError('')

    try {
      const user = handleUserLogIn(email, password)

      router.push('/account')
    } catch (err) {
      setError('Invalid email or password. Please try again.')
      console.error('Login error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleBackToHome = () => {
    router.push('/')
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

      {/* Top navigation */}
      <div className="relative z-20 flex justify-between items-center p-6">
        <button
          onClick={handleBackToHome}
          className="flex items-center space-x-2 text-gray-700 font-medium cursor-pointer hover:text-gray-900 transition-colors duration-300"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          <span>Back to Home</span>
        </button>

        <div className="text-2xl font-black text-gray-900">
          Clippy
          <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            AI
          </span>
        </div>
      </div>

      <div className="relative z-10 flex items-center justify-center min-h-screen px-4 -mt-20">
        <div className="max-w-md w-full mx-auto">
          <div
            className={`transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
          >
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 p-8">
              <div className="text-center mb-8">
                <h1 className="text-3xl font-black text-gray-900 mb-2">
                  Welcome Back
                </h1>
                <p className="text-gray-600">
                  Sign in to your ClippyAI account
                </p>
              </div>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              <div className="space-y-6">
                <div>
                  <label
                    htmlFor="email"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-4 focus:ring-purple-100 
                             focus:border-purple-500 transition-all duration-300 outline-none"
                    placeholder="Enter your email"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-4 focus:ring-purple-100 
                             focus:border-purple-500 transition-all duration-300 outline-none"
                    placeholder="Enter your password"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">
                      Remember me
                    </span>
                  </label>
                  <button
                    type="button"
                    className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                  >
                    Forgot password?
                  </button>
                </div>

                <button
                  onClick={() => handleLogin}
                  disabled={isLoading}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold 
                           rounded-lg hover:shadow-lg transition-all duration-300 transform hover:scale-105
                           focus:outline-none focus:ring-4 focus:ring-purple-300 disabled:opacity-50 
                           disabled:cursor-not-allowed disabled:transform-none"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Signing In...
                    </div>
                  ) : (
                    'Sign In'
                  )}
                </button>
              </div>

              <div className="mt-8 text-center">
                <p className="text-gray-600">
                  Don't have an account?{' '}
                  <button
                    className="text-purple-600 hover:text-purple-700 font-medium cursor-pointer"
                    onClick={() => {
                      router.push('/auth/signup')
                    }}
                  >
                    Sign up here
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-50 to-transparent opacity-50"></div>
    </div>
  )
}
