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

def load_user_history(user_id: str) -> List[Dict[str, str]]:
    """Load chat history for a user from the database"""
    conversations = db.get_recent_conversations(user_id)
    chat_history = []
    for conv in conversations:
        # Add the user's task
        chat_history.append({"role": "user", "content": conv[3]})  # task
        # Add the assistant's response
        response = f"""📝 Essay: {conv[5]}\n\n✍️ Plan: {conv[4]}\n\n💭 Critique: {conv[6]}"""
        chat_history.append({"role": "assistant", "content": response})
    return chat_history

def process_request(message: str, chat_history: List[Dict[str, str]], user_state) -> Tuple[str, List[Dict[str, str]], str]:
    # Get or create user_id from state
    user_id = user_state or str(uuid.uuid4())
    
    # Ensure user exists in database
    db.create_or_get_user(user_id, f"user_{user_id[:8]}")
    
    try:
        # Get user's conversation history if chat history is empty
        if not chat_history:
            chat_history = load_user_history(user_id)
        
        # Get last conversation summary
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
        
        # Format response with safe get operations
        response = f"""📝 Here's your essay:

{result.get('draft', 'No draft generated')}

✍️ Writing Process:
1. Plan: {result.get('plan', 'No plan generated')}
2. Critique: {result.get('critique', 'No critique available')}

🔍 Previous Context: {context if context else 'No previous context'}"""
        
        # Update chat history with proper message format
        chat_history = chat_history or []
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": response})
        
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        chat_history = chat_history or []
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": error_message})
    
    return "", chat_history, user_id

def chat_interface():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# AI Essay Writer & Assistant")
        gr.Markdown("I can help you write essays on any topic. Your conversation history will be preserved!")
        
        # Add user ID display
        user_id_text = gr.Textbox(
            label="Your User ID (Save this to continue your session later)",
            interactive=False
        )
        
        chatbot = gr.Chatbot(
            label="Chat History",
            height=600,
            type="messages"
        )
        
        msg = gr.Textbox(label="Your message", placeholder="Type your essay topic here...")
        user_state = gr.State()
        
        # Add user ID input for returning users
        user_id_input = gr.Textbox(
            label="Enter your User ID to continue previous session",
            placeholder="Enter your previous User ID here..."
        )
        
        def load_session(user_id: str) -> Tuple[str, List[Dict[str, str]], str]:
            if not user_id:
                return "", [], None
            
            # Verify user exists
            user = db.create_or_get_user(user_id, f"user_{user_id[:8]}")
            if not user:
                return "", [], None
                
            # Load chat history
            chat_history = load_user_history(user_id)
            return "", chat_history, user_id
        
        user_id_input.submit(
            load_session,
            [user_id_input],
            [msg, chatbot, user_state]
        )
        
        def update_user_id(user_id):
            return user_id if user_id else "No user ID yet. Send a message to get one!"
        
        # Update user ID display when state changes
        user_state.change(
            update_user_id,
            [user_state],
            [user_id_text]
        )
        
        msg.submit(process_request, [msg, chatbot, user_state], [msg, chatbot, user_state])
        
        gr.Examples(
            examples=[
                "Write an essay about climate change",
                "Write a persuasive essay about the importance of education",
                "Write an analytical essay about artificial intelligence"
            ],
            inputs=msg,
            label="Example Topics"
        )
    
    return demo

if __name__ == "__main__":
    demo = chat_interface()
    demo.launch(share=True)
