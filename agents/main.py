"""
Healthcare Assistant Agent using Strands Agents framework.
FastAPI implementation for AgentCore Runtime deployment.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timezone
from strands import Agent

# Initialize FastAPI app
app = FastAPI(title="Healthcare Assistant Agent", version="1.0.0")

# Healthcare assistant system prompt
HEALTHCARE_SYSTEM_PROMPT = """
You are a healthcare assistant designed to help medical professionals with:
- Patient information management
- Appointment scheduling
- Medical knowledge base queries
- Document processing and analysis

Always respond in Spanish (LATAM) unless specifically requested otherwise.
Maintain professional medical standards and patient confidentiality.
Be helpful, accurate, and professional in all interactions.
"""

# Initialize Strands agent
strands_agent = Agent(
    system_prompt=HEALTHCARE_SYSTEM_PROMPT
)


class InvocationRequest(BaseModel):
    input: Dict[str, Any]


class InvocationResponse(BaseModel):
    output: Dict[str, Any]


@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """
    Main AgentCore invocation endpoint for healthcare assistant.
    """
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        result = strands_agent(user_message)
        response = {
            "message": result.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "healthcare-assistant",
            "capabilities": ["patient_info", "appointments", "knowledge_base", "documents"]
        }

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")


@app.get("/ping")
async def ping():
    """Health check endpoint required by AgentCore Runtime."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
