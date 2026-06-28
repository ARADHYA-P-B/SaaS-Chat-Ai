import os
import security
from dotenv import load_dotenv
import asyncio
import bcrypt
from fastapi import FastAPI, Query,Depends,HTTPException,status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm  import Session
import database,models,security
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage,AIMessage


load_dotenv()

#Auto-create table in your local database file on boot
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title ="AI Saas Backend MVP")
llm = ChatOpenAI(model="gpt-4o-mini",streaming=True,temperature=0.7)


class UserAuthSchema(BaseModel):
    email :EmailStr
    password :str

@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: UserAuthSchema, db: Session = Depends(database.get_db)):
    # Check if account already exists
    existing_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    # Hash password before committing to disk storage
    secured_password = security.hash_password(payload.password)
    new_user = models.User(email=payload.email, hashed_password=secured_password)
    
    db.add(new_user)
    db.commit()
    return {"message": "Account created successfully"}

@app.post("/api/auth/login")
def login(payload: UserAuthSchema, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    # Create security authorization pass token
    token = security.create_access_token(data={"user_id": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer"}

# Allow your React frontenfd to communicate with this backend 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Streaming-enable LLM
async def ai_stream_generator(prompt:str):

    """ Asynchronously calls the llm and Yield characters as they generate."""
    try:
        message = [HumanMessage(content=prompt)]

        # Use .astream() to pull chunks token-by-token asynchrously
        async for chunk in llm.astream(message):
            ## Formatted using Server-Sent Event (SSE) standard protocal
            yield f"data : {chunk.content} \n\n"
            await asyncio.sleep(0.01)

    except Exception as e:
        yield f"data :[ERROR : {str(e)}]"

async def database_backed_stream(prompt: str, session_id: int, db: Session):
    # 1. Fetch historical chat logs from Postgres to feed context back to the AI
    history = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.created_at.asc()).all()
    
    compiled_messages = []
    for msg in history:
        if msg.role == "user":
            compiled_messages.append(HumanMessage(content=msg.content))
        else:
            compiled_messages.append(AIMessage(content=msg.content))
            
    # Add the current prompt the user just typed
    compiled_messages.append(HumanMessage(content=prompt))
    
    # Save the user's prompt immediately to the database
    user_log = models.ChatMessage(session_id=session_id, role="user", content=prompt)
    db.add(user_log)
    db.commit()

    # 2. Open our AI streaming channel
    full_ai_response = ""
    async for chunk in llm.astream(compiled_messages):
        full_ai_response += chunk.content
        yield f"data: {chunk.content}\n\n"

    # 3. Once stream closes completely, save the full response text to history log 
    ai_log = models.ChatMessage(session_id=session_id, role="assistant", content=full_ai_response)
    db.add(ai_log)
    db.commit()

@app.get("/api/chat/stream")
async def chat_stream(
    prompt :str,
    session_id :int,
    token:str,
    db:Session = Depends(database.get_db)
):
    # 1. Decode and validate the token
    user_info = security.verify_access_token(token)
    current_user_id = user_info["user_id"]

    # 2. Look up the requested chat session
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user_id  # <-- Ensure security isolation!
    ).first()
    
    # 3. If the session doesn't exist (or belongs to a different user), create a clean one
    if not session:
        session = models.ChatSession(user_id=current_user_id)
        db.add(session)
        db.commit()
        db.refresh(session)

    return StreamingResponse(
        database_backed_stream(prompt,session.id.db),
        media_type = "text/event-stream"
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1",port =8000,reload =True)

  