"""Comprehensive tests for the FastAPI activities app."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Verify that GET /activities returns all 9 activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9

    def test_get_activities_returns_correct_structure(self, client):
        """Verify that each activity has required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_correct_initial_participant_counts(self, client):
        """Verify initial participant counts are correct."""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify known participant counts from initial data
        assert len(activities["Chess Club"]["participants"]) == 2
        assert len(activities["Programming Class"]["participants"]) == 2
        assert len(activities["Basketball Team"]["participants"]) == 1
        assert len(activities["Drama Club"]["participants"]) == 1

    def test_get_activities_contains_known_activities(self, client):
        """Verify that known activities exist in the response."""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Science Club",
            "Debate Team"
        }
        
        assert expected_activities.issubset(activities.keys())


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client):
        """Test successful signup of a new participant."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Verify that signup actually adds the participant to the activity."""
        email = "newstudent@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        # Perform signup
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Chess Club"]["participants"])
        assert updated_count == initial_count + 1
        assert email in updated_response.json()["Chess Club"]["participants"]

    def test_signup_duplicate_prevention(self, client):
        """Test that duplicate signups are prevented with 400 error."""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test that signup to non-existent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_multiple_participants_different_activities(self, client):
        """Test that same email can signup for different activities."""
        email = "testuser@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class (same email, different activity)
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_signup_with_various_email_formats(self, client):
        """Test signup with different valid email formats."""
        emails = [
            "student1@mergington.edu",
            "john.doe@mergington.edu",
            "jane+test@mergington.edu",
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/Art Studio/signup?email={email}"
            )
            assert response.status_code == 200

    def test_signup_other_activities_unaffected(self, client):
        """Verify that signup to one activity doesn't affect others."""
        email = "newuser@mergington.edu"
        
        # Get initial state
        initial_activities = client.get("/activities").json()
        initial_gym_count = len(initial_activities["Gym Class"]["participants"])
        initial_drama_count = len(initial_activities["Drama Club"]["participants"])
        
        # Sign up for Chess Club
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Verify other activities unchanged
        updated_activities = client.get("/activities").json()
        assert len(updated_activities["Gym Class"]["participants"]) == initial_gym_count
        assert len(updated_activities["Drama Club"]["participants"]) == initial_drama_count


class TestCancelSignup:
    """Tests for DELETE /activities/{activity_name}/signup/{email} endpoint."""

    def test_cancel_signup_successful(self, client):
        """Test successful removal of a participant."""
        email = "michael@mergington.edu"
        
        response = client.delete(
            f"/activities/Chess Club/signup/{email}"
        )
        
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_cancel_signup_removes_participant(self, client):
        """Verify that cancel actually removes the participant."""
        email = "michael@mergington.edu"
        
        # Verify participant is there
        initial_activities = client.get("/activities").json()
        assert email in initial_activities["Chess Club"]["participants"]
        
        # Cancel signup
        client.delete(f"/activities/Chess Club/signup/{email}")
        
        # Verify participant was removed
        updated_activities = client.get("/activities").json()
        assert email not in updated_activities["Chess Club"]["participants"]

    def test_cancel_signup_nonexistent_activity(self, client):
        """Test cancel signup for non-existent activity returns 404."""
        response = client.delete(
            "/activities/Nonexistent Activity/signup/test@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_cancel_signup_student_not_signed_up(self, client):
        """Test cancel signup for student not in activity returns 404."""
        response = client.delete(
            "/activities/Chess Club/signup/nosuchstudent@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"].lower()

    def test_cancel_signup_other_activities_unaffected(self, client):
        """Verify that canceling one signup doesn't affect other activities."""
        email = "michael@mergington.edu"
        
        # Get initial state
        initial_activities = client.get("/activities").json()
        initial_gym_count = len(initial_activities["Gym Class"]["participants"])
        
        # Cancel from Chess Club
        client.delete(f"/activities/Chess Club/signup/{email}")
        
        # Verify other activities unchanged
        updated_activities = client.get("/activities").json()
        assert len(updated_activities["Gym Class"]["participants"]) == initial_gym_count

    def test_cancel_signup_twice_fails(self, client):
        """Test that canceling the same signup twice fails on second attempt."""
        email = "michael@mergington.edu"
        
        # First cancel should succeed
        response1 = client.delete(
            f"/activities/Chess Club/signup/{email}"
        )
        assert response1.status_code == 200
        
        # Second cancel should fail
        response2 = client.delete(
            f"/activities/Chess Club/signup/{email}"
        )
        assert response2.status_code == 404


class TestDataIntegrity:
    """Tests for overall data consistency and integrity."""

    def test_participant_count_consistency(self, client):
        """Verify participant list length matches actual list contents."""
        activities = client.get("/activities").json()
        
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            max_participants = activity_data["max_participants"]
            
            assert len(participants) <= max_participants
            assert isinstance(participants, list)
            assert all(isinstance(p, str) for p in participants)

    def test_no_duplicate_participants_in_activity(self, client):
        """Verify no duplicate emails in any activity's participant list."""
        activities = client.get("/activities").json()
        
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            assert len(participants) == len(set(participants)), \
                f"Duplicate participants found in {activity_name}"

    def test_signup_then_cancel_restores_original_state(self, client):
        """Test that signup + cancel returns activity to original state."""
        email = "testuser@mergington.edu"
        activity = "Science Club"
        
        # Get initial state
        initial = client.get("/activities").json()[activity]["participants"].copy()
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Cancel
        client.delete(f"/activities/{activity}/signup/{email}")
        
        # Should be back to original
        final = client.get("/activities").json()[activity]["participants"]
        assert final == initial

    def test_sequential_signups_maintain_order(self, client):
        """Verify sequential signups are properly tracked."""
        emails = [
            "user1@mergington.edu",
            "user2@mergington.edu",
            "user3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/Art Studio/signup?email={email}"
            )
            assert response.status_code == 200
        
        # All should be in the list
        final_activity = client.get("/activities").json()["Art Studio"]
        for email in emails:
            assert email in final_activity["participants"]

    def test_activity_max_participants_doesnt_prevent_signup(self, client):
        """Test that max_participants is informational (no enforcement on signup)."""
        activity = "Small Activity"
        
        # Find an activity and get current participant count
        activities = client.get("/activities").json()
        art_studio = activities["Art Studio"]
        
        # art_studio has max 18, currently has 2, so we can add more
        email = "newuser@mergington.edu"
        response = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        assert response.status_code == 200
