import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateCurrentUser,
  UserCredential,
  getAuth,
} from 'firebase/auth'

import { firebaseAuth } from './config'

export async function handleUserSignUp(
  email: string,
  password: string
): Promise<UserCredential | null> {
  try {
    const userCredentials = await createUserWithEmailAndPassword(
      firebaseAuth,
      email,
      password
    )

    return userCredentials
  } catch (error: any) {
    console.log(error)
  }

  return null
}

export function handleUserLogIn(email: string, password: string) {
  signInWithEmailAndPassword(firebaseAuth, email, password)
    .then((userCredential) => {
      return userCredential.user
    })
    .catch((error) => {
      throw error
    })
}
