"""
Smoke tests for Flask application.

These tests verify basic functionality:
- App can be created without errors
- Public routes are accessible
- Routes render without template errors
- Database is initialized correctly
"""
import pytest


class TestAppCreation:
    """Test that the Flask app can be created successfully."""
    
    def test_app_exists(self, app):
        """Verify the app instance is created."""
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_app_is_flask(self, app):
        """Verify the app is a Flask instance."""
        from flask import Flask
        assert isinstance(app, Flask)
    
    def test_database_configured(self, app):
        """Verify database URI is set."""
        assert 'SQLALCHEMY_DATABASE_URI' in app.config
        assert 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']


class TestPublicRoutes:
    """Test publicly accessible routes."""
    
    def test_home_page_loads(self, client):
        """Test the home page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Home' in response.data
    
    def test_login_page_get(self, client):
        """Test the login page loads."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'form' in response.data
    
    def test_home_contains_welcome(self, client):
        """Test home page has expected content."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Welcome' in response.data or b'Home' in response.data


class TestRouteRegistration:
    """Test that routes are registered correctly."""
    
    def test_blueprint_registered(self, app):
        """Verify the boundary blueprint is registered."""
        assert 'boundary' in app.blueprints
    
    def test_public_routes_exist(self, app):
        """Verify key public routes exist."""
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/' in rules
        assert '/login' in rules
        assert '/logout' in rules
    
    def test_protected_routes_exist(self, app):
        """Verify protected routes are registered."""
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        # Check at least one protected route per role exists
        assert any('/admin/' in rule for rule in rules)
        assert any('/csr/' in rule for rule in rules)
        assert any('/pin/' in rule for rule in rules)
        assert any('/pm/' in rule for rule in rules)


class TestDatabaseInitialization:
    """Test that database tables are created."""
    
    def test_db_tables_created(self, app_context):
        """Verify database tables exist."""
        from app import db
        
        # Get all table names
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Verify at least some expected tables exist
        # (entity tables created by create_all() in create_app)
        assert len(tables) > 0  # At least some tables should exist
    
    def test_db_can_query(self, app_context):
        """Verify we can perform basic database queries."""
        from app import db
        
        # Simple connection test
        result = db.session.execute(db.text("SELECT 1")).fetchone()
        assert result[0] == 1


class TestTemplateRendering:
    """Test that templates render without errors."""
    
    def test_index_renders(self, client):
        """Test index template renders."""
        response = client.get('/')
        assert response.status_code == 200
        # Should not have Jinja2 template errors
        assert b'{{' not in response.data
        assert b'{%' not in response.data
    
    def test_login_renders(self, client):
        """Test login template renders."""
        response = client.get('/login')
        assert response.status_code == 200
        # Should contain form element
        assert b'<form' in response.data


class TestProtectedRoutesRedirect:
    """Test that protected routes redirect when not logged in."""
    
    @pytest.mark.parametrize("route", [
        "/admin/dashboard",
        "/csr/dashboard",
        "/pin/dashboard",
        "/pm/dashboard",
    ])
    def test_protected_route_requires_login(self, client, route):
        """Test protected routes redirect to login."""
        response = client.get(route, follow_redirects=False)
        # Should redirect (302) or unauthorized (401)
        assert response.status_code in [302, 401]
    
    def test_logout_requires_login(self, client):
        """Test logout route requires authentication."""
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code in [302, 401]


class TestImports:
    """Test that critical imports work."""
    
    def test_import_create_app(self):
        """Test create_app can be imported."""
        from app import create_app
        assert create_app is not None
    
    def test_import_db(self):
        """Test db can be imported."""
        from app import db
        assert db is not None
    
    def test_import_login_manager(self):
        """Test login_manager can be imported."""
        from app import login_manager
        assert login_manager is not None
    
    def test_import_routes_module(self):
        """Test routes module exists."""
        import app.boundary.routes
        assert app.boundary.routes is not None


class TestAppConfiguration:
    """Test Flask app configuration."""
    
    def test_secret_key_set(self, app):
        """Verify SECRET_KEY is configured."""
        assert app.config['SECRET_KEY'] is not None
        assert len(app.config['SECRET_KEY']) > 0
    
    def test_testing_mode(self, app):
        """Verify app is in testing mode."""
        assert app.config['TESTING'] is True
    
    def test_csrf_disabled_for_testing(self, app):
        """Verify CSRF is disabled in testing."""
        # CSRF should be disabled or not enforced
        assert app.config.get('WTF_CSRF_ENABLED', True) is False


class TestClientBasics:
    """Test test client basic functionality."""
    
    def test_client_exists(self, client):
        """Verify test client is created."""
        assert client is not None
    
    def test_client_can_make_requests(self, client):
        """Verify client can make HTTP requests."""
        response = client.get('/')
        assert response is not None
        assert hasattr(response, 'status_code')
        assert hasattr(response, 'data')
    
    def test_client_follows_redirects(self, client):
        """Verify client can follow redirects."""
        # Accessing protected route should redirect to login
        response = client.get('/admin/dashboard', follow_redirects=True)
        assert response.status_code == 200
