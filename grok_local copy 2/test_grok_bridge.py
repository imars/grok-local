import unittest
import threading
import time
import requests
from http.server import HTTPServer
from unittest.mock import patch
from grok_bridge import app  # Assuming the previous code is in grok_bridge.py

class TestGrokBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the Flask app in a separate thread with retry logic."""
        cls.server_thread = threading.Thread(target=app.run, kwargs={
            'host': '0.0.0.0',
            'port': 5000,
            'debug': False,
            'threaded': True
        })
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Retry loop to ensure server is ready
        cls.base_url = 'http://localhost:5000'
        max_attempts = 10
        delay = 1  # seconds
        for attempt in range(max_attempts):
            try:
                response = requests.get(f'{cls.base_url}/channel', timeout=1)
                if response.status_code == 200:
                    print(f"Server started successfully after {attempt + 1} attempts")
                    break
            except (requests.ConnectionError, requests.Timeout):
                print(f"Waiting for server to start (attempt {attempt + 1}/{max_attempts})...")
                time.sleep(delay)
        else:
            raise Exception("Server failed to start within allotted time")

    def setUp(self):
        """Clear the global state before each test."""
        with app.test_client() as client:
            # Reset the responses and current_request
            global responses, current_request
            from grok_bridge import responses, current_request
            responses.clear()
            current_request = None

    # Mock any potential external calls (currently not used, but ready for future expansion)
    @patch('requests.get')  # Example: mocking requests.get for future web searches
    def test_channel_post_valid(self, mock_get):
        """Test POST to /channel with valid data."""
        # Configure mock response if needed in future
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "Mocked response"

        payload = {'input': 'What is 2 + 2?', 'id': 'test123'}
        response = requests.post(f'{self.base_url}/channel', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'Request posted')
        self.assertEqual(data['id'], 'test123')
        
        # Check if current_request was set
        with app.test_client() as client:
            get_response = client.get('/channel')
            self.assertIn('Input: "What is 2 + 2?"', get_response.data.decode())
            self.assertIn('Identifier: "test123"', get_response.data.decode())

    def test_channel_post_invalid(self):
        """Test POST to /channel with invalid data."""
        # Missing 'id'
        payload = {'input': 'Test'}
        response = requests.post(f'{self.base_url}/channel', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid request data')

        # Empty payload
        response = requests.post(f'{self.base_url}/channel', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid request data')

    def test_response_logging(self):
        """Test logging a response via /response."""
        params = {'id': 'test456', 'response': 'The answer is 4'}
        response = requests.get(f'{self.base_url}/response', params=params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'Response received')

        # Check if response was stored
        with app.test_client() as client:
            from grok_bridge import responses
            self.assertIn('test456', responses)
            self.assertEqual(responses['test456'], 'The answer is 4')

    def test_get_response(self):
        """Test retrieving a response from /get-response."""
        # Set up a response first
        with app.test_client() as client:
            from grok_bridge import responses
            responses['test789'] = 'Hello, world!'

        response = requests.get(f'{self.base_url}/get-response', params={'id': 'test789'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'Hello, world!')

        # Test non-existent ID
        response = requests.get(f'{self.base_url}/get-response', params={'id': 'nonexistent'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.text, 'No response yet')

    def test_channel_get_no_request(self):
        """Test GET /channel when no request has been posted."""
        response = requests.get(f'{self.base_url}/channel')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'No request posted yet.')

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Flask doesn't have a built-in shutdown, so we'll let the daemon thread die with the process
        pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
