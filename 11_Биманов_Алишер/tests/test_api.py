import asyncio
import sys
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
import time

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.mark.asyncio
async def test_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        username = f"testuser_{int(time.time())}"
        response = await client.post("/users/register/", json={"username": username, "password": "testpass"})
        assert response.status_code == 201
        response = await client.post("/users/login/", json={"username": username, "password": "testpass"})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        username = f"testuser_{int(time.time())}"
        response = await client.post("/users/register/", json={"username": username, "password": "testpass"})
        assert response.status_code == 201

        login_response = await client.post("/users/login/", json={"username": username, "password": "testpass"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a note
        note_data = {"title": "Test Note", "content": "This is a test note."}
        response = await client.post("/notes", json=note_data, headers=headers)
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Read the note
        response = await client.get(f"/notes/{note_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Test Note"

        # Update the note
        update_data = {"title": "Updated Note", "content": "This is an updated test note."}
        response = await client.put(f"/notes/{note_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Note"

        # Delete the note
        response = await client.delete(f"/notes/{note_id}", headers=headers)
        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/notes/{note_id}", headers=headers)
        assert response.status_code == 404

