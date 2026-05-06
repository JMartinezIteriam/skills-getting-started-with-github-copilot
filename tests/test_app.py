import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Test GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status code"""
        # Arrange
        expected_status_code = 200

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == expected_status_code

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert isinstance(data, dict)

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing '{field}' in {activity_name}"


class TestSignupForActivity:
    """Test POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        # Arrange
        email = "testuser@mergington.edu"
        activity_name = "Chess%20Club"
        expected_status = 200

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == expected_status
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity returns 404"""
        # Arrange
        email = "test@mergington.edu"
        activity_name = "NonExistent%20Club"
        expected_status = 404
        expected_detail = "Activity not found"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        data = response.json()

        # Assert
        assert response.status_code == expected_status
        assert data["detail"] == expected_detail

    def test_signup_duplicate_registration(self):
        """Test that duplicate registration returns 400 error"""
        # Arrange
        email = "duplicate_checker@mergington.edu"
        activity_name = "Chess%20Club"
        expected_error_status = 400

        # Act - First signup
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response1.status_code == 200

        # Act - Second signup with same email
        response2 = client.post(f"/activities/{activity_name}/signup?email={email}")
        data = response2.json()

        # Assert
        assert response2.status_code == expected_error_status
        assert "already signed up" in data["detail"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        email = "newstudent_checker@mergington.edu"
        activity_name = "Chess Club"

        # Act - Get count before signup
        response_before = client.get("/activities")
        activities_before = response_before.json()
        participants_before = len(activities_before[activity_name]["participants"])

        # Act - Perform signup
        client.post(f"/activities/Chess%20Club/signup?email={email}")

        # Act - Get count after signup
        response_after = client.get("/activities")
        activities_after = response_after.json()
        participants_after = len(activities_after[activity_name]["participants"])

        # Assert
        assert participants_after == participants_before + 1
        assert email in activities_after[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Test DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # Arrange
        email = "unregister_user@mergington.edu"
        activity_name = "Chess%20Club"
        expected_status = 200

        # Act - First signup
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act - Then unregister
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        data = response.json()

        # Assert
        assert response.status_code == expected_status
        assert email in data["message"]

    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity returns 404"""
        # Arrange
        email = "test@mergington.edu"
        activity_name = "NonExistent%20Club"
        expected_status = 404
        expected_detail = "Activity not found"

        # Act
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        data = response.json()

        # Assert
        assert response.status_code == expected_status
        assert data["detail"] == expected_detail

    def test_unregister_participant_not_found(self):
        """Test unregister of non-existent participant returns 404"""
        # Arrange
        email = "nonexistent@mergington.edu"
        activity_name = "Chess%20Club"
        expected_status = 404
        expected_detail = "Participant not found"

        # Act
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        data = response.json()

        # Assert
        assert response.status_code == expected_status
        assert data["detail"] == expected_detail

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        # Arrange
        email = "removeme_checker@mergington.edu"
        activity_name = "Chess Club"
        encoded_activity = "Chess%20Club"

        # Act - Signup
        client.post(f"/activities/{encoded_activity}/signup?email={email}")

        # Act - Verify signup
        response_check = client.get("/activities")
        assert email in response_check.json()[activity_name]["participants"]

        # Act - Unregister
        client.delete(f"/activities/{encoded_activity}/unregister?email={email}")

        # Act - Verify removal
        response_after = client.get("/activities")

        # Assert
        assert email not in response_after.json()[activity_name]["participants"]
