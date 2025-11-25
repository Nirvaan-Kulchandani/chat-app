from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime
import os
from dotenv import load_dotenv

from database import SessionLocal, engine, init_db, Message
from manager import ConnectionManager
from ai_service import AIService

# Load environment variables
load_dotenv()

# Initialize Database
init_db()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

manager = ConnectionManager()
ai_service = AIService()

@app.get("/")
async def get():
    return FileResponse('static/index.html')

@app.get("/api/history/{session_id}")
async def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    return messages

@app.post("/api/chat/ai")
async def chat_ai(data: dict, db: Session = Depends(get_db)):
    user_message = data.get("message")
    session_id = data.get("session_id")
    
    if not user_message or not session_id:
        raise HTTPException(status_code=400, detail="Missing message or session_id")

    # Save user message
    db_msg = Message(content=user_message, sender="user", session_id=session_id, type="text")
    db.add(db_msg)
    
    # Get AI response
    ai_response = await ai_service.get_response(user_message, session_id)
    
    # Save AI response
    db_ai_msg = Message(content=ai_response, sender="ai", session_id=session_id, type="text")
    db.add(db_ai_msg)
    db.commit()
    
    return {"response": ai_response}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Save to DB (optional for transient chat, but good for history)
            # For now, we just broadcast. In a real app, we'd save it.
            # Let's save it for persistence.
            db_msg = Message(content=data, sender=f"User {client_id}", session_id="global_human_chat", type="text")
            db.add(db_msg)
            db.commit()
            
            await manager.broadcast(f"User {client_id}: {data}", sender=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"User {client_id} left the chat")
