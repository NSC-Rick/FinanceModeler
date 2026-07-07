"""
ElevenLabs Conversational AI Widget Component
"""
import streamlit.components.v1 as components

def render_elevenlabs_widget(agent_id: str):
    """
    Render the ElevenLabs conversational AI widget.
    
    Args:
        agent_id: The ElevenLabs agent ID
    """
    html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="margin: 0; padding: 0;">
            <elevenlabs-convai agent-id="{agent_id}"></elevenlabs-convai>
            <script src="https://unpkg.com/@elevenlabs/convai-widget-embed" type="text/javascript"></script>
        </body>
        </html>
    """
    
    components.html(html_code, height=0, scrolling=False)
