import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: 'AIzaSyBpcFq4xeXM_W2c-ZorZcd_TyB1cSOLEqM',
  authDomain: 'spurhacks25.firebaseapp.com',
  projectId: 'spurhacks25',
  storageBucket: 'spurhacks25.firebasestorage.app',
  messagingSenderId: '543525172744',
  appId: '1:543525172744:web:34035c064ce554746183bd',
  measurementId: 'G-J2XH6HEL7V',
}

// Initialize Firebase
const firebaseApp = initializeApp(firebaseConfig)
const firebaseAuth = getAuth(firebaseApp)

export { firebaseApp, firebaseAuth }
