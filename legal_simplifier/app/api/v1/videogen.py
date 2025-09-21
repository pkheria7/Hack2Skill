import time
import os
import requests
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from google.genai import Client
from google.genai import types

router = APIRouter()

# Pydantic model for the request body
class VideoGenRequest(BaseModel):
    prompt: str
    uid: str

# A simple in-memory store for demonstration purposes
# In a production app, use a database like Redis or PostgreSQL
video_jobs = {}

# Placeholder for the actual video generation function
def generate_video_task(job_id: str, prompt: str):
    """
    Simulates a long-running video generation task.
    In a real application, this would call a service like Google Veo.
    """
    try:
        # Step 1: Initialize the client (replace with your actual API key handling)
        client = Client(api_key=os.environ.get('GOOGLE_API_KEY'))

        # Step 2: Call the generate_videos model (hypothetical)
        # This part is based on how other Google generative AI APIs work
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=prompt,
        )

        # Update job status
        video_jobs[job_id] = {"status": "in_progress"}

        # Step 3: Poll the operation status (this can be a long-running process)
        while not operation.done:
            print("Waiting for video generation to complete...")
            time.sleep(10)
            operation = client.operations.get(operation.name)

        # Step 4: Access and download the video
        if 'generateVideoResponse' in operation.response:
            generated_samples = operation.response['generateVideoResponse']['generatedSamples']
            if generated_samples:
                video_uri = generated_samples[0]['video']['uri']
                
                # IMPORTANT: Securely download the video. Do not append key to URL.
                # A more secure method would be to use a signed URL or stream the data directly.
                # For this example, we'll use a direct download for simplicity.
                api_key = os.environ.get('GOOGLE_API_KEY')
                download_url = f"{video_uri}&key={api_key}" # This is still insecure for production!
                
                response = requests.get(download_url)
                if response.status_code == 200:
                    filename = f"video_{job_id}.mp4"
                    filepath = os.path.join("generated_videos", filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    
                    video_jobs[job_id]["status"] = "completed"
                    video_jobs[job_id]["video_url"] = f"/api/v1/videos/{filename}"
                else:
                    video_jobs[job_id]["status"] = "failed"
                    video_jobs[job_id]["error"] = "Failed to download video."
            else:
                video_jobs[job_id]["status"] = "failed"
                video_jobs[job_id]["error"] = "No video samples generated."
        else:
            video_jobs[job_id]["status"] = "failed"
            video_jobs[job_id]["error"] = "Unexpected API response format."

    except Exception as e:
        video_jobs[job_id] = {"status": "failed", "error": str(e)}

@router.post("/videogen/start")
async def start_video_generation(req: VideoGenRequest, background_tasks: BackgroundTasks):
    """
    Starts a new video generation job.
    """
    job_id = f"job-{int(time.time())}"
    video_jobs[job_id] = {"status": "queued", "uid": req.uid, "prompt": req.prompt}
    background_tasks.add_task(generate_video_task, job_id, req.prompt)
    return {"job_id": job_id}

@router.get("/videogen/status/{job_id}")
async def get_video_status(job_id: str):
    """
    Retrieves the status and URL of a video generation job.
    """
    job = video_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# Optional: Endpoint to serve the generated video file
@router.get("/videos/{filename}")
async def serve_video(filename: str):
    filepath = os.path.join("generated_videos", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Use FastAPI's FileResponse to serve the video
    from fastapi.responses import FileResponse
    return FileResponse(path=filepath, media_type="video/mp4")