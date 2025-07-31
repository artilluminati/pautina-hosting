import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.routers import admin, auth, hosts, users
from app import models
from app.core.security import get_password_hash
import os

# Используем тестовый PostgreSQL или SQLite по умолчанию
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:"
)
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

# Create a FastAPI app for testing
@pytest.fixture(scope="session")
def app():
    Base.metadata.create_all(bind=engine)
    app = FastAPI()
    app.include_router(auth.router, prefix="/auth")
    app.include_router(users.router, prefix="/users")
    app.include_router(hosts.router, prefix="/hosts")
    app.include_router(admin.router, prefix="/admin")
    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture

def create_user(db_session):
    def _create_user(phone, email, password, name="test", role=models.RoleEnum.user):
        hashed = get_password_hash(password)
        user = models.User(phone=phone, name=name, email=email, hashed_password=hashed, role=role)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user

@pytest.fixture

def auth_token(client, create_user):
    # create and login a normal user
    phone, email, pwd = "+10000000000", "user@example.com", "password"
    create_user(phone, email, pwd)
    response = client.post(
        "/auth/login",
        data={"username": email, "password": pwd}
    )
    return response.json()["access_token"]

@pytest.fixture

def admin_token(client, create_user):
    # create admin user and get token
    phone, email, pwd = "+10000000001", "admin@example.com", "password"
    create_user(phone, email, pwd, role=models.RoleEnum.admin)
    response = client.post(
        "/auth/login",
        data={"username": email, "password": pwd}
    )
    return response.json()["access_token"]

# Tests for auth

def test_register_and_duplicate(client):
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "+79998887766",
        "password": "secret123",
        "agree_terms": True,
        "agree_privacy": True
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["role"] == models.RoleEnum.user.value
    assert data["active"] is True
    assert "token" in data
    assert "created_at" in data

    # Duplicate email
    payload2 = payload.copy()
    payload2.update({"name": "Alice2", "phone": "+79990001122"})
    resp2 = client.post("/auth/register", json=payload2)
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Адрес электронной почты уже зарегистрирован"

    # Duplicate phone
    payload3 = payload.copy()
    payload3.update({"name": "Alice3", "email": "alice3@example.com"})
    resp3 = client.post("/auth/register", json=payload3)
    assert resp3.status_code == 400
    assert resp3.json()["detail"] == "Номер телефона уже зарегистрирован"


def test_login_invalid(client):
    resp = client.post("/auth/login", data={"username": "noone@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_valid_after_register(client, db_session):
    # Register user
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        "password": "doesnt_matter",
        "phone": "+75556667788",
        "agree_terms": True,
        "agree_privacy": True
    }
    resp = client.post("/auth/register", json=payload)
    print("response:", resp.json())
    assert resp.status_code == 200

    temp_password = db_session.query(models.TempPassword).filter(models.TempPassword.token == resp.json().get("token")).first().temp_password
    print(temp_password)
    assert temp_password is not None, "Temp password not set on user"

    # Login with temp password
    login_resp = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": temp_password}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_recover_password(client, create_user, db_session):
    user = create_user(
        "+1234567890",
        "recover@example.com",
        "oldpass",
        name="RecoverTest"
    )
    # Ensure phone set and persisted
    user.phone = "+1234567890"
    db_session.add(user)
    db_session.commit()

    resp = client.post("/auth/recover", json={"phone": user.phone})
    assert resp.status_code == 200
    data = resp.json()
    assert data["login"] == user.email
    assert isinstance(data["password"], str)
    assert len(data["password"]) >= 6

    # New password works
    login_resp = client.post(
        "/auth/login",
        data={"username": data["login"], "password": data["password"]}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_recover_password_user_not_found(client):
    resp = client.post("/auth/recover", json={"phone": "+0000000000"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User with this phone not found"

# Tests for users/me

def test_read_users_me(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"

# Tests for hosts

def test_create_list_get_host(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {"subdomain": "testdomain", "plan": models.PlanEnum.demo.value}
    resp = client.post("/hosts/", headers=headers, json=payload)
    assert resp.status_code == 200
    host_data = resp.json()
    assert host_data["subdomain"] == payload["subdomain"]
    assert host_data["plan"] == payload["plan"]
    host_id = host_data["id"]

    # List hosts
    resp2 = client.get("/hosts/", headers=headers)
    assert resp2.status_code == 200
    assert any(h["id"] == host_id for h in resp2.json())

    # Get host detail
    resp3 = client.get(f"/hosts/{host_id}", headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["id"] == host_id

    # Non-existent
    resp4 = client.get("/hosts/999", headers=headers)
    assert resp4.status_code == 404

# Tests for admin routes

def test_admin_list_forbidden(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.get("/admin/users", headers=headers)
    assert resp.status_code == 403


def test_admin_list_success(client, admin_token, create_user):
    # Create users
    create_user("+10111112222", "u1@example.com", "p1")
    create_user("+10111113333", "u2@example.com", "p2")
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/admin/users", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_admin_block_archive(client, admin_token, create_user):
    user = create_user("+10222223333", "howner@example.com", "pwd")
    db = TestingSessionLocal()
    host = models.Host(subdomain="h1", plan=models.PlanEnum.demo, owner_id=user.id)
    db.add(host)
    db.commit()
    db.refresh(host)
    host_id = host.id
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}
    # Block
    resp = client.post(f"/admin/hosts/{host_id}/block", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Host blocked"

    # Archive
    resp2 = client.post(f"/admin/hosts/{host_id}/archive", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["detail"] == "Host archived"

    # Non-existent
    resp3 = client.post("/admin/hosts/999/block", headers=headers)
    assert resp3.status_code == 404
