import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import docker
from fastapi import APIRouter, HTTPException, Depends
from ..deps import get_db
from ...datamodel import Team

router = APIRouter()
client = docker.from_env()


# Base directory where team configs are stored
TEAM_CONFIGS_DIR = Path("team_configs")


@router.get("/{team_id}/")
async def deploy_team(team_id: int, user_id: str, db=Depends(get_db)):
    """
    Deploy a team configuration as a Docker container.

    Args:
        team_id: The ID of the team to deploy

    Returns:
        Deployment status and container information
    """
    # Get the team from database
    response = db.get(Team, filters={"id": team_id, "user_id": user_id})
    if not response.status or not response.data:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team_data = response.data[0].model_dump()
    
    # Path to the Dockerfile directory
    dockerfile_path = Path("/Users/gourabsinha/Desktop/AiPlanet/codebase/deployed-application")
    
    # Write the team configuration from the database directly to the Dockerfile directory
    team_config_path = dockerfile_path / "team.json"
    with open(team_config_path, 'w') as f:
        json.dump(team_data.get("component", {}), f)
    
    # Build the Docker image
    image_name = f"agent-server-{team_id}"
    image_tag = "latest"

    try:
        # Build the image
        image, build_logs = client.images.build(
            path=str(dockerfile_path),  # Path to the directory containing Dockerfile
            dockerfile="Dockerfile",  # Name of the Dockerfile
            tag=f"{image_name}:{image_tag}",
            rm=True,  # Remove intermediate containers
        )

        # Run the container
        container = client.containers.run(
            f"{image_name}:{image_tag}",
            detach=True,
            ports={"8084/tcp": ("0.0.0.0", 8084)},  # Map container port to host
            environment={
                "TEAM_CONFIG_PATH": "/app/team.json"
            },
            name=f"agent-server-{team_id}",
            remove=True,  # Remove container when stopped
        )

        return {
            "status": "deployed",
            "team_id": team_id,
            "container_id": container.id,
            "container_name": container.name,
            "url": "http://localhost:8084",
        }

    except docker.errors.BuildError as e:
        raise HTTPException(status_code=500, detail=f"Docker build error: {str(e)}")
    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment error: {str(e)}")
    finally:
        # Clean up the team configuration file after deployment
        if team_config_path.exists():
            team_config_path.unlink()


@router.delete("/deployment/{team_id}/")
async def stop_deployment(team_id: str):
    """
    Stop and remove a deployed team container.

    Args:
        team_id: The ID of the team to stop

    Returns:
        Stop status
    """
    container_name = f"agent-server-{team_id}"

    try:
        container = client.containers.get(container_name)
        container.stop()
        return {"status": "stopped", "team_id": team_id}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"No deployment found for team: {team_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping deployment: {str(e)}")
