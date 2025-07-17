from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from meta import lifespan
from users import router as users_router
from notes import router as notes_router
import uvicorn
from typing import List

app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(notes_router)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/ws-test", response_class=HTMLResponse)
async def get_ws_test():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Chat</title>
    </head>
    <body>
        <h2>WebSocket Chat</h2>
        <input id=\"messageInput\" type=\"text\" autocomplete=\"off\" placeholder=\"Type a message...\"/>
        <button onclick=\"sendMessage()\">Send</button>
        <ul id=\"messages\"></ul>
        <script>
            let ws = new WebSocket(`ws://${location.host}/ws`);
            ws.onmessage = function(event) {
                let messages = document.getElementById('messages');
                let li = document.createElement('li');
                li.textContent = event.data;
                messages.appendChild(li);
            };
            function sendMessage() {
                let input = document.getElementById('messageInput');
                ws.send(input.value);
                input.value = '';
            }
        </script>
    </body>
    </html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A user disconnected")

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)