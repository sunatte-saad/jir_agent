from fastapi import FastAPI, Request, HTTPException
from phi_jira_agent_final import get_phi_jira_agent
import httpx
import os

app = FastAPI(
    title="Phi Jira Teams Bot API",
    description="Simplified API to interact with Phi Jira Agent via Teams",
    version="1.0.0"
)

agent = get_phi_jira_agent()

# Bot credentials - set these as environment variables
MICROSOFT_APP_ID = os.environ.get("MICROSOFT_APP_ID", "")
MICROSOFT_APP_PASSWORD = os.environ.get("MICROSOFT_APP_PASSWORD", "")
MICROSOFT_APP_TENANT_ID =os.environ.get("MICROSOFT_APP_TENANT_ID", "")

async def get_bot_token():
    """Get OAuth token from Microsoft Bot Framework"""
    # Use tenant ID or "common" for multi-tenant apps
    url = f"https://login.microsoftonline.com/{MICROSOFT_APP_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": MICROSOFT_APP_ID,
        "client_secret": MICROSOFT_APP_PASSWORD,
        "scope": "https://api.botframework.com/.default"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        if response.status_code == 200:
            return response.json()["access_token"]
        
        # Log detailed error
        error_detail = response.text
        print(f"Token request failed: {response.status_code}")
        print(f"Error response: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Failed to get bot token: {error_detail}")

async def send_reply_to_teams(activity, reply_text, token):
    """Send reply back to Teams using Bot Framework API"""
    service_url = activity.get("serviceUrl")
    conversation_id = activity.get("conversation", {}).get("id")
    activity_id = activity.get("id")
    
    reply_url = f"{service_url}/v3/conversations/{conversation_id}/activities/{activity_id}"
    
    reply_activity = {
        "type": "message",
        "text": reply_text,
        "from": activity.get("recipient"),
        "recipient": activity.get("from"),
        "replyToId": activity_id
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(reply_url, json=reply_activity, headers=headers)
        return response.status_code

@app.post("/api/messages")
async def messages(req: Request):
    """
    Endpoint for Azure Bot Service to send activities (messages) from Teams.
    Teams sends a standard Activity JSON payload.
    """
    try:
        activity = await req.json()
        
        # Ignore non-message activities
        if activity.get("type") != "message":
            return {"status": "ignored"}
        
        user_text = activity.get("text", "").strip()
        if not user_text:
            return {"status": "ok"}
        
        # Get bot token
        token = await get_bot_token()
        
        # Run your Jira agent
        reply_text = agent.run(user_text,stream=False)
        
        # Send reply back to Teams
        status_code = await send_reply_to_teams(activity, reply_text, token)
        
        if status_code in [200, 201, 202]:
            return {"status": "ok"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to send reply: {status_code}")

    except Exception as e:
        # Log the error and try to send error message to Teams if possible
        print(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok", "agent": "Phi Jira Agent ready"}