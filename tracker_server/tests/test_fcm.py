<<<<<<< HEAD
import os

from dotenv import load_dotenv
from unittest.mock import Mock
import pytest

from app.external_dependencies.fcm import FCM
from app.types_classes import NotifType

load_dotenv(os.path.join('.secrets', '.env'))

@pytest.fixture(scope="module")
def my_fcm():
    CRED = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') 
    mock_db = Mock()
    mock_db.get_doc.return_value = 'fhsfc6eZTqGbBA4roX_BTa:APA91bEATox4iW2TJ9XVkWoqG3j3JMkR0eJgLPxWZRkNnPinIxtBJL5pS5-Ho8Xr-BhE-0kI-tA_rIijSZCsZ83CrV2aC0QTNd-OJO981eKC5iQBZW8tPDk6BX7TX0uLm3xj5Y3f8KWM'
    return FCM(CRED, mock_db)

@pytest.mark.parametrize(
    ('type', 'data', 'output'), (
          (NotifType.CREDS, None, ('Update Your Login', 'Please update your login information for Meross.')),
          (NotifType.PEAK, {"app_name":'tv'}, ('Peak Usage Alert','Try to use tv after 5 PM. Click here to turn it off.'))  
    )
)
def test_map_message(my_fcm, type, data, output):
    assert my_fcm.map_message(type, data) == output
    
def test_notify(my_fcm):
    assert 'powereye1-e599e' in my_fcm.notify('test user', NotifType.PEAK, {'app_name':'tv'})
    
    
from unittest.mock import Mock
=======
from unittest.mock import Mock
>>>>>>> 9b2bd7eba719ba18966a3008de8ef080da999da4
from app.external_dependencies.fcm import FCM
from app.types_classes import NotifType


# Mock the database connection (you might need to use a testing library like unittest.mock)
class MockDB:
    def get_doc(self, collection, filter, projection):
        # Implement your own mock for database retrieval
        return {"registration_token": "mock_token"}

def fcm_instance():
    # Create and return an instance of FCM with a mock database
    db = MockDB()
    return FCM('path_to_firebase_credentials.json', db)

def test_successful_notification(fcm_instance):
    user = 'test_user'
    notification_type = NotifType.CREDS
    data = {'app_name': 'TestApp'}

    response = fcm_instance.notify(user, notification_type, data)
    # You can add assertions here to check if the response is as expected

def test_invalid_user(fcm_instance):
    # Test the scenario where an invalid user is provided
    pass

def test_different_notification_types(fcm_instance):
    # Test each notification type (CREDS, DISCONNECTION, GOAL, PEAK, PHANTOM, BASELINE)
    pass

def test_custom_data(fcm_instance):
    # Test with custom data and ensure the title and body include the data
    pass

def test_database_retrieval(fcm_instance):
    # Test if the database retrieval works correctly
    pass

def test_invalid_firebase_credentials(fcm_instance):
    # Test how the class handles cases with missing or invalid Firebase credentials
    pass

def test_logging(fcm_instance):
    # Test if the class logs the notifications correctly
    pass

def test_response_handling(fcm_instance):
    # Test how the class handles different response statuses from Firebase
    pass

def test_edge_cases(fcm_instance):
    # Test edge cases, such as very long data values, empty data, and special characters
    pass

def test_exception_handling(fcm_instance):
    # Test how the class handles exceptions that might be raised during the notification process
    pass

