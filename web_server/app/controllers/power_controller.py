
# app\controllers\appliance_controller.py
from flask import jsonify
from app.models.appliance_model import Appliance
from app.models.user_model import User
from app.models.power_model import Power


# Define a function to get the most recent power reading for a specific appliance
def get_most_recent_reading(user_id, appliance_id):
    try:
        # Get the user by ID
        user = User.objects.get(id=user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404  # Return a response if user not found

        # Get the most recent power reading for the specified appliance
        power_reading = Power.objects(user=user).order_by('-timestamp').first()

        # Check if the power_reading exists and has the specified appliance_id as a field
        if power_reading and hasattr(power_reading, appliance_id):
            # Retrieve the power value using getattr
            power_value = getattr(power_reading, appliance_id)
            return jsonify({'power': power_value}), 200  # Return the power value
        else:
            return jsonify({'error': 'No power data available for this appliance.'}), 404  # Return an error message

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Handle exceptions and return an error message if needed