"""Test WebSocket connection to the backend."""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/conversation"
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")
            
            # Wait for connection established message
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Send a heartbeat
            await websocket.send(json.dumps({"type": "heartbeat"}))
            print("Sent heartbeat")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            print("✓ WebSocket is working!")
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket())
