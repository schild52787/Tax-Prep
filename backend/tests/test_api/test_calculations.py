"""Tests for calculation and PDF API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as ac:
        yield ac


@pytest.fixture
async def return_id(client):
    """Create a tax return and add W-2 data for testing."""
    # Create return
    resp = await client.post(
        "/api/v1/returns/",
        json={"return_name": "Calc Test Return", "filing_status": "single"},
    )
    assert resp.status_code == 201
    rid = resp.json()["id"]

    # Add taxpayer
    await client.put(
        f"/api/v1/returns/{rid}/taxpayer/primary",
        json={
            "first_name": "John",
            "middle_initial": "Q",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "street_address": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62701",
        },
    )

    # Add W-2
    await client.post(
        f"/api/v1/returns/{rid}/income/w2",
        json={
            "employer_name": "ACME Corp",
            "box_1_wages": 75000,
            "box_2_fed_tax_withheld": 10000,
        },
    )

    return rid


@pytest.mark.asyncio
async def test_run_calculation(client, return_id):
    """Test running a tax calculation."""
    resp = await client.post(f"/api/v1/returns/{return_id}/calculate")
    assert resp.status_code == 200
    data = resp.json()

    assert data["return_id"] == return_id
    assert data["total_income"] > 0
    assert data["agi"] > 0
    assert data["taxable_income"] > 0
    assert data["total_tax"] > 0
    assert data["deduction_method"] in ("standard", "itemized")
    assert "form_1040" in data["required_forms"]


@pytest.mark.asyncio
async def test_get_calculation(client, return_id):
    """Test getting a calculation result after running it."""
    # First run the calculation
    await client.post(f"/api/v1/returns/{return_id}/calculate")

    # Then get it
    resp = await client.get(f"/api/v1/returns/{return_id}/calculation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["return_id"] == return_id
    assert data["total_income"] > 0


@pytest.mark.asyncio
async def test_get_calculation_not_found(client, return_id):
    """Test getting calculation before running it."""
    resp = await client.get(f"/api/v1/returns/{return_id}/calculation")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_calculate_nonexistent_return(client):
    """Test calculating for a non-existent return."""
    resp = await client.post("/api/v1/returns/nonexistent/calculate")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_recalculate_updates_result(client, return_id):
    """Test that running calculation twice updates the existing result."""
    resp1 = await client.post(f"/api/v1/returns/{return_id}/calculate")
    data1 = resp1.json()

    # Add more income
    await client.post(
        f"/api/v1/returns/{return_id}/income/w2",
        json={
            "employer_name": "Side Gig",
            "box_1_wages": 25000,
            "box_2_fed_tax_withheld": 3000,
        },
    )

    resp2 = await client.post(f"/api/v1/returns/{return_id}/calculate")
    data2 = resp2.json()

    # Total income should be higher with the second W-2
    assert data2["total_income"] > data1["total_income"]


@pytest.mark.asyncio
async def test_download_summary_pdf(client, return_id):
    """Test downloading the summary PDF."""
    # First run calculation
    await client.post(f"/api/v1/returns/{return_id}/calculate")

    # Download summary
    resp = await client.get(f"/api/v1/returns/{return_id}/pdf/summary")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert b"%PDF" in resp.content[:10]


@pytest.mark.asyncio
async def test_download_summary_without_calculation(client, return_id):
    """Test that summary download fails without a calculation."""
    resp = await client.get(f"/api/v1/returns/{return_id}/pdf/summary")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_download_forms_without_calculation(client, return_id):
    """Test that forms download fails without a calculation."""
    resp = await client.get(f"/api/v1/returns/{return_id}/pdf/forms")
    assert resp.status_code == 400
