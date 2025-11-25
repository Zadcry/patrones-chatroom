import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# 1. Configurar SQLite en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Fixture para la Base de Datos
@pytest.fixture(scope="function")
def db_session():
    """Crea tablas nuevas para cada test y las borra al final"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# 3. Fixture para el Cliente (Sobreescribiendo la dependencia de DB)
@pytest.fixture(scope="function")
def client(db_session):
    """Cliente de pruebas que usa la DB temporal"""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    # Reemplazamos la dependencia real (Postgres) por la de Test (SQLite)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()