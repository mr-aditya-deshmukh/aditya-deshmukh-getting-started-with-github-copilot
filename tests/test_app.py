"""
Tests for the Mergington High School Activities API
"""
import pytest
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Save original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, reset_activities):
        """Test that get activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, reset_activities):
        """Test that get activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, reset_activities):
        """Test that get activities returns expected activity names"""
        response = client.get("/activities")
        activities_data = response.json()
        
        expected_activities = [
            "Debate Club",
            "Robotics Club",
            "Basketball",
            "Tennis",
            "Drama Club",
            "Art Studio",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in activities_data
    
    def test_get_activities_contains_required_fields(self, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_details in activities_data.items():
            for field in required_fields:
                assert field in activity_details


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, reset_activities):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Debate%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]
    
    def test_signup_updates_participants_list(self, reset_activities):
        """Test that signup updates the participants list"""
        email = "newstudent@mergington.edu"
        client.post("/activities/Debate%20Club/signup", params={"email": email})
        
        response = client.get("/activities")
        assert email in response.json()["Debate Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, reset_activities):
        """Test that signing up the same participant twice fails"""
        email = "alex@mergington.edu"
        
        # Try to sign up someone already in the activity
        response = client.post(
            "/activities/Debate%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_fails(self, reset_activities):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_increments_participant_count(self, reset_activities):
        """Test that signup increments the participant count"""
        activity_name = "Chess Club"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        
        assert count_after == count_before + 1


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, reset_activities):
        """Test unregistering an existing participant"""
        response = client.post(
            "/activities/Debate%20Club/unregister",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        assert "alex@mergington.edu" in response.json()["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister removes participant from the list"""
        email = "alex@mergington.edu"
        client.post("/activities/Debate%20Club/unregister", params={"email": email})
        
        response = client.get("/activities")
        assert email not in response.json()["Debate Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, reset_activities):
        """Test that unregistering a nonexistent participant fails"""
        response = client.post(
            "/activities/Debate%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity_fails(self, reset_activities):
        """Test that unregistering from a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_decrements_participant_count(self, reset_activities):
        """Test that unregister decrements the participant count"""
        activity_name = "Debate%20Club"
        response_before = client.get("/activities")
        count_before = len(response_before.json()["Debate Club"]["participants"])
        
        client.post(f"/activities/{activity_name}/unregister", params={"email": "alex@mergington.edu"})
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()["Debate Club"]["participants"])
        
        assert count_after == count_before - 1


class TestRoot:
    """Tests for GET / endpoint"""
    
    def test_root_redirects(self):
        """Test that root endpoint redirects"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
