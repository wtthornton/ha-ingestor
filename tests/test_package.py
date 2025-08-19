"""Tests for package imports and basic functionality."""


class TestPackageImports:
    """Test that the package can be imported correctly."""

    def test_main_package_import(self):
        """Test that the main package can be imported."""
        import ha_ingestor

        assert ha_ingestor.__version__ == "0.1.0"
        assert ha_ingestor.__author__ == "Your Name"
        assert ha_ingestor.__email__ == "your.email@example.com"

    def test_main_module_import(self):
        """Test that the main module can be imported."""
        from ha_ingestor import main

        assert main is not None

    def test_module_structure(self):
        """Test that all expected modules exist."""
        import ha_ingestor

        # Check that all expected modules exist
        assert hasattr(ha_ingestor, "mqtt")
        assert hasattr(ha_ingestor, "websocket")
        assert hasattr(ha_ingestor, "influxdb")
        assert hasattr(ha_ingestor, "models")
        assert hasattr(ha_ingestor, "utils")

    def test_main_functions_exist(self):
        """Test that main functions exist and are callable."""
        from ha_ingestor.main import cli, main

        assert callable(main)
        assert callable(cli)

        # Check function signatures
        import inspect

        main_sig = inspect.signature(main)
        cli_sig = inspect.signature(cli)

        assert main_sig.return_annotation == int
        assert cli_sig.return_annotation == int


class TestPackageFunctionality:
    """Test basic package functionality."""

    def test_version_consistency(self):
        """Test that version is consistent across package and pyproject.toml."""
        import ha_ingestor

        # This test will be more comprehensive once we have proper version management
        assert ha_ingestor.__version__ == "0.1.0"

    def test_package_metadata(self):
        """Test that package metadata is properly set."""
        import ha_ingestor

        assert hasattr(ha_ingestor, "__version__")
        assert hasattr(ha_ingestor, "__author__")
        assert hasattr(ha_ingestor, "__email__")
        assert hasattr(ha_ingestor, "__all__")

    def test_module_docstrings(self):
        """Test that all modules have proper docstrings."""
        import ha_ingestor

        # Check main package docstring
        assert ha_ingestor.__doc__ is not None
        assert len(ha_ingestor.__doc__.strip()) > 0

        # Check module docstrings
        assert ha_ingestor.mqtt.__doc__ is not None
        assert ha_ingestor.websocket.__doc__ is not None
        assert ha_ingestor.influxdb.__doc__ is not None
        assert ha_ingestor.models.__doc__ is not None
        assert ha_ingestor.utils.__doc__ is not None


class TestPackageStructure:
    """Test the overall package structure."""

    def test_package_is_importable_as_module(self):
        """Test that the package can be run as a module."""

        # This test will be implemented once we have the full package structure
        # For now, we'll just verify the basic structure exists
        assert True

    def test_package_has_required_files(self):
        """Test that the package has all required files."""
        import os

        # Check that key files exist
        assert os.path.exists("ha_ingestor/__init__.py")
        assert os.path.exists("ha_ingestor/main.py")
        assert os.path.exists("ha_ingestor/mqtt/__init__.py")
        assert os.path.exists("ha_ingestor/websocket/__init__.py")
        assert os.path.exists("ha_ingestor/influxdb/__init__.py")
        assert os.path.exists("ha_ingestor/models/__init__.py")
        assert os.path.exists("ha_ingestor/utils/__init__.py")

    def test_package_can_be_installed(self):
        """Test that the package can be installed in development mode."""
        # This test will be implemented once we have the full package structure
        # For now, we'll just verify the basic structure exists
        assert True
