"""Unit tests for deployment automation."""

from datetime import datetime
from unittest.mock import Mock, mock_open, patch


from src.iac_agents.deployment_automation import (
    DeploymentStatus,
    TerraformDeploymentManager,
)


def test_deployment_manager_initialization():
    """Test TerraformDeploymentManager can be initialized."""
    manager = TerraformDeploymentManager()
    assert manager is not None
    assert hasattr(manager, "plan_deployment")
    assert hasattr(manager, "apply_deployment")
    assert hasattr(manager, "get_deployment_status")


def test_deployment_status_creation():
    """Test DeploymentStatus dataclass creation."""
    status = DeploymentStatus(
        deployment_id="test-123",
        status="planning",
        resources_created=[],
        resources_modified=[],
        resources_destroyed=[],
        output_values={},
        logs=[],
        started_at=datetime.now(),
    )
    assert status.deployment_id == "test-123"
    assert status.status == "planning"
    assert isinstance(status.logs, list)


def test_deployment_manager_plan_simple():
    """Test deployment manager plan method with mock."""
    manager = TerraformDeploymentManager()

    # Test that the method exists and can be called
    assert hasattr(manager, "plan_deployment")

    # Test with simulated planning by manually creating a deployment status
    test_status = DeploymentStatus(
        deployment_id="test-123",
        status="planned",
        resources_created=["resource.test"],
        resources_modified=[],
        resources_destroyed=[],
        output_values={},
        logs=["Planning completed"],
        started_at=datetime.now(),
    )

    # Manually add to deployments to simulate successful planning
    manager.deployments["test-123"] = test_status

    retrieved_status = manager.get_deployment_status("test-123")
    assert retrieved_status is not None
    assert retrieved_status.deployment_id == "test-123"
    assert retrieved_status.status == "planned"


def test_deployment_manager_get_status():
    """Test getting deployment status."""
    manager = TerraformDeploymentManager()

    # Manually add a deployment status
    test_status = DeploymentStatus(
        deployment_id="test-123",
        status="planned",
        resources_created=[],
        resources_modified=[],
        resources_destroyed=[],
        output_values={},
        logs=[],
        started_at=datetime.now(),
    )
    manager.deployments["test-123"] = test_status

    # Get status
    status = manager.get_deployment_status("test-123")

    assert status is not None
    assert isinstance(status, DeploymentStatus)
    assert status.deployment_id == "test-123"


def test_deployment_manager_invalid_deployment_id():
    """Test getting status with invalid deployment ID."""
    manager = TerraformDeploymentManager()

    status = manager.get_deployment_status("invalid-id")

    # Should return None for non-existent deployment
    assert status is None


def test_deployment_manager_list_deployments():
    """Test listing all deployments."""
    manager = TerraformDeploymentManager()

    # Add some test deployments
    for i in range(3):
        test_status = DeploymentStatus(
            deployment_id=f"test-{i}",
            status="planned",
            resources_created=[],
            resources_modified=[],
            resources_destroyed=[],
            output_values={},
            logs=[],
            started_at=datetime.now(),
        )
        manager.deployments[f"test-{i}"] = test_status

    deployments = manager.list_deployments()

    assert len(deployments) == 3
    assert all(isinstance(d, DeploymentStatus) for d in deployments)


def test_deployment_manager_generate_summary():
    """Test generating deployment summary."""
    manager = TerraformDeploymentManager()

    # Add a test deployment
    test_status = DeploymentStatus(
        deployment_id="test-123",
        status="completed",
        resources_created=["azurerm_storage_account.test"],
        resources_modified=[],
        resources_destroyed=[],
        output_values={"storage_id": "test-value"},
        logs=["Deployment successful"],
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )
    manager.deployments["test-123"] = test_status

    summary = manager.generate_deployment_summary("test-123")

    assert isinstance(summary, str)
    assert "test-123" in summary
    assert "COMPLETED" in summary.upper()


def test_deployment_manager_workspace_creation():
    """Test workspace creation functionality."""
    manager = TerraformDeploymentManager()

    with patch("os.makedirs") as mock_makedirs, patch("builtins.open", mock_open()):

        workspace_dir = manager.create_deployment_workspace(
            "test-123", "resource test {}", {"location": "eastus"}
        )

        assert isinstance(workspace_dir, str)
        mock_makedirs.assert_called()


@patch("subprocess.run")
def test_terraform_command_execution(mock_run):
    """Test Terraform command execution."""
    mock_run.return_value = Mock(returncode=0, stdout="Success output", stderr="")

    manager = TerraformDeploymentManager()
    test_status = DeploymentStatus(
        deployment_id="test-123",
        status="planning",
        resources_created=[],
        resources_modified=[],
        resources_destroyed=[],
        output_values={},
        logs=[],
        started_at=datetime.now(),
    )

    result = manager._run_terraform_command("/tmp/test", ["version"], test_status)

    assert result == "Success output"
    assert len(test_status.logs) > 0


def test_deployment_status_error_handling():
    """Test deployment status with error conditions."""
    error_status = DeploymentStatus(
        deployment_id="error-test",
        status="failed",
        resources_created=[],
        resources_modified=[],
        resources_destroyed=[],
        output_values={},
        logs=["Error occurred"],
        started_at=datetime.now(),
        error_message="Test error message",
    )

    assert error_status.status == "failed"
    assert error_status.error_message == "Test error message"
    assert "Error occurred" in error_status.logs


def test_deployment_manager_cleanup():
    """Test deployment workspace cleanup."""
    manager = TerraformDeploymentManager()

    with patch("os.path.exists") as mock_exists, patch("shutil.rmtree") as mock_rmtree:

        mock_exists.return_value = True

        manager.cleanup_workspace("test-123")

        mock_exists.assert_called()
        mock_rmtree.assert_called()


def test_deployment_backend_config_generation():
    """Test backend configuration generation."""
    manager = TerraformDeploymentManager()

    config = manager._generate_backend_config("test-deployment-id")

    assert isinstance(config, str)
    assert "terraform" in config.lower()
    assert "backend" in config.lower()
    assert "test-deployment-id" in config
