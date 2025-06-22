import { NextResponse } from 'next/server'
import AWS from 'aws-sdk'

const s3 = new AWS.S3({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
})

export async function GET() {
  try {
    const data = await s3
      .listObjectsV2({
        Bucket: process.env.S3_BUCKET_NAME!,
        Prefix: '', // add 'videos/' if your files are in a folder
      })
      .promise()

    const mp4Files = data.Contents?.filter((file) =>
      file.Key?.endsWith('.mp4')
    ).map((file) => {
      return `https://${process.env.S3_BUCKET_NAME}.s3.${process.env.AWS_REGION}.amazonaws.com/${file.Key}`
    })

    return NextResponse.json({ videos: mp4Files || [] })
  } catch (error) {
    console.error(error)
    return NextResponse.json(
      { error: 'Error fetching S3 videos' },
      { status: 500 }
    )
  }
}
