"""Tests for the tax returns API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_return(client):
    response = await client.post(
        "/api/v1/returns/",
        json={
            "return_name": "Test Return 2025",
            "tax_year": 2025,
            "filing_status": "single",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["return_name"] == "Test Return 2025"
    assert data["tax_year"] == 2025
    assert data["filing_status"] == "single"
    assert data["status"] == "in_progress"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_returns(client):
    # Create a return first
    await client.post(
        "/api/v1/returns/",
        json={"return_name": "Test", "tax_year": 2025, "filing_status": "single"},
    )

    response = await client.get("/api/v1/returns/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_return(client):
    create_resp = await client.post(
        "/api/v1/returns/",
        json={"return_name": "Get Test", "tax_year": 2025, "filing_status": "single"},
    )
    return_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/returns/{return_id}")
    assert response.status_code == 200
    assert response.json()["id"] == return_id


@pytest.mark.asyncio
async def test_update_return(client):
    create_resp = await client.post(
        "/api/v1/returns/",
        json={"return_name": "Before", "tax_year": 2025, "filing_status": "single"},
    )
    return_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/returns/{return_id}",
        json={"return_name": "After", "filing_status": "married_filing_jointly"},
    )
    assert response.status_code == 200
    assert response.json()["return_name"] == "After"
    assert response.json()["filing_status"] == "married_filing_jointly"


@pytest.mark.asyncio
async def test_delete_return(client):
    create_resp = await client.post(
        "/api/v1/returns/",
        json={"return_name": "Delete Me", "tax_year": 2025, "filing_status": "single"},
    )
    return_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/returns/{return_id}")
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(f"/api/v1/returns/{return_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_return_not_found(client):
    response = await client.get("/api/v1/returns/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_w2(client):
    create_resp = await client.post(
        "/api/v1/returns/",
        json={"return_name": "W2 Test", "tax_year": 2025, "filing_status": "single"},
    )
    return_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/returns/{return_id}/income/w2",
        json={
            "employer_name": "Acme Corp",
            "employer_ein": "12-3456789",
            "box_1_wages": 75000,
            "box_2_fed_tax_withheld": 9500,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["employer_name"] == "Acme Corp"
    assert data["box_1_wages"] == 75000


@pytest.mark.asyncio
async def test_taxpayer_crud(client):
    create_resp = await client.post(
        "/api/v1/returns/",
        json={"return_name": "TP Test", "tax_year": 2025, "filing_status": "single"},
    )
    return_id = create_resp.json()["id"]

    # Create primary taxpayer
    response = await client.put(
        f"/api/v1/returns/{return_id}/taxpayer/primary",
        json={"first_name": "John", "last_name": "Doe", "ssn": "123-45-6789"},
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"
    # SSN should NOT be in response
    assert "ssn" not in response.json()

    # Get primary taxpayer
    response = await client.get(f"/api/v1/returns/{return_id}/taxpayer/primary")
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"


@pytest.mark.asyncio
async def test_dependent_crud(client):
    create_resp = await client.post(
        "/api/v1/returns/",
        json={"return_name": "Dep Test", "tax_year": 2025, "filing_status": "single"},
    )
    return_id = create_resp.json()["id"]

    # Add dependent
    response = await client.post(
        f"/api/v1/returns/{return_id}/taxpayer/dependents",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "relationship_to_taxpayer": "daughter",
            "date_of_birth": "2015-06-15",
        },
    )
    assert response.status_code == 201
    dep_id = response.json()["id"]

    # List dependents
    response = await client.get(f"/api/v1/returns/{return_id}/taxpayer/dependents")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Delete dependent
    response = await client.delete(
        f"/api/v1/returns/{return_id}/taxpayer/dependents/{dep_id}"
    )
    assert response.status_code == 204
