import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add src to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirect(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the get activities endpoint"""
    
    def test_get_all_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected activities are present
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Soccer Club", "Art Club",
            "Drama Club", "Debate Club", "Science Club"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_structure(self):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test the signup endpoint"""
    
    def test_signup_valid_activity(self):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
    
    def test_signup_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_already_signed_up(self):
        """Test signing up for an activity when already registered"""
        # First signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        
        # Attempt duplicate signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "duplicate@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_multiple_activities(self):
        """Test that a student can sign up for multiple activities"""
        email = "multi@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""
    
    def test_unregister_valid_activity(self):
        """Test unregistering from an activity"""
        email = "unregister@mergington.edu"
        
        # First signup
        client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Drama Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_not_signed_up(self):
        """Test unregistering when not signed up for the activity"""
        response = client.delete(
            "/activities/Soccer Club/unregister",
            params={"email": "notsigned@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"


class TestActivityParticipantTracking:
    """Test that participant tracking works correctly"""
    
    def test_participants_updated_on_signup(self):
        """Test that participants list is updated after signup"""
        email = "tracking@mergington.edu"
        
        # Get initial state
        response_before = client.get("/activities")
        participants_before = response_before.json()["Science Club"]["participants"]
        
        # Sign up
        client.post(
            "/activities/Science Club/signup",
            params={"email": email}
        )
        
        # Get updated state
        response_after = client.get("/activities")
        participants_after = response_after.json()["Science Club"]["participants"]
        
        assert email in participants_after
        assert len(participants_after) == len(participants_before) + 1
    
    def test_participants_updated_on_unregister(self):
        """Test that participants list is updated after unregister"""
        email = "tracking2@mergington.edu"
        
        # Sign up first
        client.post(
            "/activities/Debate Club/signup",
            params={"email": email}
        )
        
        # Get state before unregister
        response_before = client.get("/activities")
        participants_before = response_before.json()["Debate Club"]["participants"]
        
        # Unregister
        client.delete(
            "/activities/Debate Club/unregister",
            params={"email": email}
        )
        
        # Get updated state
        response_after = client.get("/activities")
        participants_after = response_after.json()["Debate Club"]["participants"]
        
        assert email not in participants_after
        assert len(participants_after) == len(participants_before) - 1
