import unittest
from unittest.mock import patch
from api import index as service

class ServiceTests(unittest.TestCase):
    def setUp(self): self.client = service.app.test_client()
    def test_get_renders(self): self.assertEqual(self.client.get("/").status_code, 200)
    def test_blank_and_oversized_queries_rejected(self):
        for query in ["", " " , "x" * 121]:
            self.assertEqual(self.client.post("/", data={"song": query}).status_code, 400)
    def test_unconfigured_service_never_calls_provider(self):
        with patch.object(service, "CLIENT_SECRET", ""), patch.object(service.requests, "post") as call:
            self.assertEqual(self.client.post("/", data={"song": "Example"}).status_code, 503)
            call.assert_not_called()
    def test_timeout_is_handled_without_exposing_provider_details(self):
        with patch.object(service, "CLIENT_ID", "id"), patch.object(service, "CLIENT_SECRET", "secret"), patch.object(service, "LASTFM_API_KEY", "key"), patch.object(service.requests, "post", side_effect=service.requests.Timeout("private provider diagnostic")):
            response=self.client.post("/", data={"song":"Example"})
            self.assertEqual(response.status_code,503)
            self.assertNotIn(b"private provider diagnostic",response.data)
    def test_token_request_has_timeout(self):
        with patch.object(service.requests,"post") as call:
            call.return_value.json.return_value={"access_token":"test"}
            self.assertEqual(service.get_spotify_token(),"test")
            self.assertEqual(call.call_args.kwargs["timeout"],(3,10))

if __name__ == "__main__": unittest.main()
