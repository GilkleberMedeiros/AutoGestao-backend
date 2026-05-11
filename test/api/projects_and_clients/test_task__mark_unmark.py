import uuid
from test.api.projects_and_clients.test_task__upd import BaseTaskTestCase


class TasksRoute_MarkUnmark(BaseTaskTestCase):
  def test_mark_task_as_done_success_outcome_validation(self):
    token = self._get_valid_token()

    # Verify task starts as not done
    self.task_obj.refresh_from_db()
    self.assertFalse(self.task_obj.is_done)

    res = self.client.patch(
      f"/{self.task_obj.id}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertTrue(res_data["is_done"])

    # Verify DB was updated
    self.task_obj.refresh_from_db()
    self.assertTrue(self.task_obj.is_done)

  def test_unmark_task_as_done_success_outcome_validation(self):
    token = self._get_valid_token()

    # Mark task as done first
    self.task_obj.is_done = True
    self.task_obj.save()

    res = self.client.patch(
      f"/{self.task_obj.id}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertFalse(res_data["is_done"])

    # Verify DB was updated
    self.task_obj.refresh_from_db()
    self.assertFalse(self.task_obj.is_done)

  def test_mark_unmark_task_toggle_multiple_times(self):
    token = self._get_valid_token()

    # First toggle: False -> True
    res1 = self.client.patch(
      f"/{self.task_obj.id}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res1.status_code, 200)
    self.assertTrue(res1.json()["is_done"])

    # Second toggle: True -> False
    res2 = self.client.patch(
      f"/{self.task_obj.id}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res2.status_code, 200)
    self.assertFalse(res2.json()["is_done"])

    # Third toggle: False -> True
    res3 = self.client.patch(
      f"/{self.task_obj.id}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res3.status_code, 200)
    self.assertTrue(res3.json()["is_done"])

  def test_mark_unmark_task_response_contains_task_data(self):
    token = self._get_valid_token()

    res = self.client.patch(
      f"/{self.task_obj.id}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    res_data = res.json()

    self.assertEqual(res.status_code, 200)
    self.assertIsNotNone(res_data.get("id"))
    self.assertIsNotNone(res_data.get("name"))
    self.assertIsNotNone(res_data.get("is_done"))
    self.assertEqual(res_data["id"], str(self.task_obj.id))
    self.assertEqual(res_data["name"], self.task_obj.name)

  def test_mark_unmark_task_unauthenticated_returns_401(self):
    res = self.client.patch(f"/{self.task_obj.id}/mark-unmark")
    self.assertEqual(res.status_code, 401)

  def test_mark_unmark_task_user_invalid_email_returns_403(self):
    token = self._get_valid_token()
    self.user.is_email_valid = False
    self.user.save()
    res = self.client.patch(
      f"/{self.task_obj.id}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 403)

  def test_mark_unmark_task_invalid_id_returns_404(self):
    token = self._get_valid_token()
    res = self.client.patch(
      f"/{uuid.uuid4()}/mark-unmark", headers={"Authorization": f"Bearer {token}"}
    )
    self.assertEqual(res.status_code, 404)
    res_data = res.json()
    self.assertFalse(res_data.get("success"))
    self.assertIn("Task", res_data.get("details", ""))
