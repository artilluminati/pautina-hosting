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
    def _create_user(email, password, name="test", role=models.RoleEnum.user):
        hashed = get_password_hash(password)
        user = models.User(name=name, email=email, hashed_password=hashed, role=role)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user

@pytest.fixture
def auth_token(client, create_user):
    # register and login a normal user
    email, pwd = "user@example.com", "password"
    create_user(email, pwd)
    response = client.post("/auth/login", data={"username": email, "password": pwd})
    return response.json()["access_token"]

@pytest.fixture
def admin_token(client, create_user):
    # create admin user and get token
    email, pwd = "admin@example.com", "password"
    create_user(email, pwd, role=models.RoleEnum.admin)
    response = client.post("/auth/login", data={"username": email, "password": pwd})
    return response.json()["access_token"]

# Tests for auth

def test_register_and_duplicate(client):
    # Register new user
    resp = client.post("/auth/register", json={"name": "Alice", "email": "alice@example.com", "password": "secret"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alice@example.com"

    # Duplicate registration
    resp2 = client.post("/auth/register", json={"name": "Alice2", "email": "alice@example.com", "password": "secret2"})
    assert resp2.status_code == 400

# Tests for login

def test_login_invalid(client):
    resp = client.post("/auth/login", data={"username": "noone@example.com", "password": "x"})
    assert resp.status_code == 401

# Tests for users/me

def test_read_users_me(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"

# Tests for hosts

def test_create_list_get_host(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create host
    resp = client.post("/hosts/", headers=headers, json={"subdomain": "testdomain", "plan": "demo"})
    assert resp.status_code == 200
    host_id = resp.json()["id"]

    # List hosts
    resp2 = client.get("/hosts/", headers=headers)
    assert resp2.status_code == 200
    assert any(h["id"] == host_id for h in resp2.json())

    # Get host
    resp3 = client.get(f"/hosts/{host_id}", headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["subdomain"] == "testdomain"

    # Unauthorized get
    resp4 = client.get("/hosts/999", headers=headers)
    assert resp4.status_code == 404

# Tests for admin routes

def test_admin_list_forbidden(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.get("/admin/users", headers=headers)
    assert resp.status_code == 403


def test_admin_list_success(client, admin_token, create_user):
    # Create some users
    create_user("u1@example.com", "p1")
    create_user("u2@example.com", "p2")
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/admin/users", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_admin_block_archive(client, admin_token, create_user):
    # Create host owned by someone
    user = create_user("howner@example.com", "pwd")
    # insert host via db session
    db = TestingSessionLocal()
    host = models.Host(subdomain="h1", plan="demo", owner_id=user.id)
    db.add(host); db.commit(); db.refresh(host)
    host_id = host.id
    db.close()

    headers = {"Authorization": f"Bearer {admin_token}"}
    # block
    resp = client.post(f"/admin/hosts/{host_id}/block", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Host blocked"
    # archive
    resp2 = client.post(f"/admin/hosts/{host_id}/archive", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["detail"] == "Host archived"

    # non-existent
    resp3 = client.post("/admin/hosts/999/block", headers=headers)
    assert resp3.status_code == 404
