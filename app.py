import gradio as gr
from essay_writer import create_essay_chain
from chat_db import ChatDatabase
import json
import uuid
from typing import Dict, List, Tuple

db = ChatDatabase()

def format_conversation_history(conversations: List[Tuple]) -> str:
    if not conversations:
        return "No previous conversations found."
    
    history = "Previous Conversations:\n\n"
    for conv in conversations:
        history += f"• {conv[-1]}\n"  # conv[-1] contains the summary
    return history

def process_request(message: str, history: List[List[str]], user_id: str = None) -> Tuple[str, Dict]:
    if not user_id:
        user_id = str(uuid.uuid4())
        db.create_or_get_user(user_id, f"user_{user_id[:8]}")
    
    # Get user's conversation history
    recent_conversations = db.get_recent_conversations(user_id)
    last_summary = db.get_last_conversation_summary(user_id)
    
    # Initialize the essay chain
    chain = create_essay_chain()
    
    # Add context from last conversation if available
    context = ""
    if last_summary:
        context = f"\nContext from last conversation - Topic: {last_summary['task']}\n"
    
    # Process the request
    result = chain.invoke({
        "task": message + context,
        "content": [],
        "max_revisions": 1,
        "revision_number": 0
    })
    
    # Save to database
    db.save_conversation(user_id, result)
    
    # Format conversation history
    history_text = format_conversation_history(recent_conversations)
    
    # Format response
    response = f"""📝 Here's your essay:

{result['draft']}

✍️ Writing Process:
1. Plan: {result['plan']}
2. Critique: {result['critique']}

📚 {history_text}"""
    
    return response

def create_interface():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        user_id = gr.State(lambda: str(uuid.uuid4()))
        
        gr.Markdown("# AI Essay Writer & Assistant")
        gr.Markdown("I can help you write essays on any topic. Your conversation history will be preserved!")
        
        chatbot = gr.ChatInterface(
            fn=lambda msg, history: process_request(msg, history, user_id.value),
            examples=[
                "Write an essay about climate change",
                "Write a persuasive essay about the importance of education",
                "Write an analytical essay about artificial intelligence"
            ],
            title="Chat with AI Essay Writer"
        )
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True)
