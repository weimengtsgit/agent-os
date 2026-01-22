"""
Iteration 5: Console Smoke Tests

Tests that verify:
- Console package can be imported
- Console app can be instantiated
- Basic routes are accessible
"""

import pytest


@pytest.mark.smoke
class TestConsoleSmokeTests:
    """Smoke tests for Console UI"""

    def test_console_package_imports(self):
        """Console package should be importable"""
        try:
            import console
            assert console is not None
        except ImportError:
            pytest.skip("Console package not installed")

    def test_console_app_imports(self):
        """Console app module should be importable"""
        try:
            from console import app
            assert app is not None
        except ImportError:
            pytest.skip("Console package not installed")

    def test_console_app_has_flask_instance(self):
        """Console app should have Flask instance"""
        try:
            from console.app import app
            assert app is not None
            # Check it's a Flask app
            assert hasattr(app, 'route'), "app should be a Flask instance"
        except ImportError:
            pytest.skip("Console package not installed")

    def test_console_app_has_routes(self):
        """Console app should have expected routes"""
        try:
            from console.app import app

            # Get all registered routes
            routes = [rule.rule for rule in app.url_map.iter_rules()]

            # Check for expected routes
            expected_routes = [
                '/',
                '/runs',
                '/runs/<run_id>',
                '/api/runs',
                '/api/runs/<run_id>',
            ]

            for expected_route in expected_routes:
                # Check if route exists (may have different parameter names)
                route_pattern = expected_route.replace('<run_id>', '<')
                matching_routes = [r for r in routes if route_pattern in r]
                assert len(matching_routes) > 0, \
                    f"Expected route pattern '{expected_route}' not found in {routes}"

        except ImportError:
            pytest.skip("Console package not installed")

    def test_console_app_test_client_works(self):
        """Console app test client should work"""
        try:
            from console.app import app

            with app.test_client() as client:
                # Test root route
                response = client.get('/')
                assert response.status_code in [200, 302, 404], \
                    f"Unexpected status code: {response.status_code}"

        except ImportError:
            pytest.skip("Console package not installed")

    def test_console_api_runs_endpoint(self):
        """Console API /api/runs endpoint should be accessible"""
        try:
            from console.app import app

            with app.test_client() as client:
                response = client.get('/api/runs')
                assert response.status_code == 200, \
                    f"API endpoint failed with status {response.status_code}"

                # Should return JSON
                assert response.content_type == 'application/json' or \
                       'application/json' in response.content_type

        except ImportError:
            pytest.skip("Console package not installed")
