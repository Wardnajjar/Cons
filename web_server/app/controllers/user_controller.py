# app\controllers\user_controller.py
from flask import jsonify ,request, send_file
from app.models.user_model import User,PlugType
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
from functools import wraps
import jwt
from app.config import Config
from app.utils.cloud_interface import cloud
import traceback
from app.utils.img_sys import *
from werkzeug.utils import secure_filename
import os
import mimetypes

def login_required(f):
    @wraps(f)  # Preserve original function metadata
    def decorated_function(*args, **kwargs): #applies the wraps decorator to preserve the name and docstring of the original function f.
        token  = request.headers.get('Authorization')# Get the JWT token from request headers
        if not token:
            return jsonify({'message': 'Token is missing'}), 401  # Return error if token is missing

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])  # Decode the token
        # except jwt.ExpiredSignatureError:
        #     return jsonify({'message': 'Token has expired. Please log in again.'}), 401  # Handle expired token
        # except jwt.DecodeError:
        #     return jsonify({'message': 'Invalid token'}), 401  # Handle invalid token
        except Exception as e:
            # output e
            print(e)
            return jsonify({
                'message': f'Token is invalid !! {e}'
            }), 401
        return f(*args, **kwargs)  # Call the original route function f if token is valid

    return decorated_function  # Return the decorated function ,This function will be used to wrap protected routes.


# Function to validate PowerEye system password
def validate_password(password):
    try:
        # Define complexity criteria
        if (
            len(password) < 8
            or not any(char.isupper() for char in password)
            or not any(char.islower() for char in password)
            or not any(char.isdigit() for char in password)
            or not any(char in '!@#$%^&*()-_+=<>,.?/:;{}[]~' for char in password)
        ):
            return False, jsonify({'message': 'Password should contain at least 8 characters, including at least one uppercase letter, one lowercase letter, one digit, and one special character'}), 400

        # Return True if the password meet the complexity criteria
        return True, None, None

    except Exception as e:
        return False, jsonify({'message': f'Error occurred while validating password: {str(e)}'}), 500
    
    
# Function to validate Meross credentials (email and password)
def validate_meross_credentials(email, password):
    try:
        # Implement validation using Meross interface
        user = {'email': email, 'password': password}  # Create user object
        return cloud.verify_credentials(PlugType.MEROSS.value, user)  # Call verify_credentials with PlugType.MEROSS
    except Exception as e:
        traceback.print_exc()
        return False, jsonify({'message': f'Error occurred while validating Meross credentials: {str(e)}'}), 500



def signup(email, power_eye_password, cloud_password):
    try:
        # Validate PowerEye system password
        is_valid_pass, error_response, status_code = validate_password(power_eye_password)
        if not is_valid_pass:
            return error_response, status_code

        # Validate Meross credentials
        if not validate_meross_credentials(email, cloud_password):
            return jsonify({'error': 'Invalid Meross credentials.'}), 400

        # Check if the email is already associated with a non-deleted user
        existing_user = User.objects(email=email, is_deleted=False).first()
        if existing_user:
            return jsonify({'error': 'Email is already registered.'}), 400

        # Encrypt the Power Eye password
        hashed_password = bcrypt.generate_password_hash(power_eye_password).decode('utf-8')
        
        # Create and save the user
        user = User(
            email=email,
            password=hashed_password,
            cloud_password=cloud_password,
            appliances=[]
        )
        # user.save()
        print("user is saved")
        return jsonify({'message': 'User created successfully.'},{user}), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



def login(email, password):
    try:
        # Validate if email is provided
        if not email:
            return jsonify({'error': 'Email is required.'}), 400

        # Validate if password is provided
        if not password:
            return jsonify({'error': 'Password is required.'}), 400

        # Find the user by email
        user = User.objects(email=email, is_deleted=False).first()
        if not user:
            return jsonify({'error': 'Invalid email or password.'}), 401

        # Validate the password
        if not user.check_password(password):
            return jsonify({'error': 'Invalid email or password.'}), 401

        # If email and password are valid, generate and return a token
        token = user.generate_token()
        
        return jsonify({'token': token}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def logout():
    return jsonify({'message': 'Logged out successfully.'}), 200


def get_user_info(user_id):
    try:
        # Retrieve the user by ID and make sure they are not deleted
        user = User.objects.get(id=user_id, is_deleted=False)

        if not user:
            return jsonify({'message': 'User not found.'}), 404
        
        user_info = {
            'email': user.email,
            'username': user.username,
            'current_month_energy': user.current_month_energy,
            'energy_goal': user.energy_goal,
            # Add other user fields as needed
        }

        return jsonify({'user_info': user_info}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_user_info(user_id, meross_password=None, power_eye_password=None, username=None, profile_picture=None):
    try:
        # Retrieve the user by ID and make sure they are not deleted
        user = User.objects.get(id=user_id, is_deleted=False)

        if not user:
            return jsonify({'message': 'User not found.'}), 404

        # Update user information if provided
        if meross_password is not None:
            user.cloud_password = meross_password

        if power_eye_password is not None:
            if not validate_password(power_eye_password):
                return jsonify({'error': 'Invalid PowerEye system password.'}), 400
            hashed_password = bcrypt.generate_password_hash(power_eye_password).decode('utf-8')
            print(user.password)
            user.password = hashed_password
            print(user.password)
            

        if username is not None:
            user.username = username

        if profile_picture is not None:
            user.profile_picture = profile_picture

        user.save()

        return jsonify({'message': 'User information updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def delete_user(user_id):
    try:
        # Retrieve the user by ID and make sure they are not deleted
        user = User.objects.get(id=user_id, is_deleted=False)

        if not user:
            return jsonify({'message': 'User not found.'}), 404

        # Soft delete the user
        user.is_deleted = True
        user.save()

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



def get_goal(user_id):
    # Retrieve the user by ID and make sure they are not deleted
    user = User.objects.get(id=user_id, is_deleted=False)

    if not user:
        return jsonify({'message': 'User not found.'}), 404
    
    goal = user.energy_goal
    return jsonify({'energy_goal': goal}), 200


def set_goal(user_id, energy):
    # Retrieve the user by ID and make sure they are not deleted
    user = User.objects.get(id=user_id, is_deleted=False)

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    # Validate the energy input
    try:
        energy = float(energy)
        if energy < 0:
            return jsonify({'message': 'Energy goal must be a positive value.'}), 400

        # Check if the input is greater than or equal to the total energy cost incurred
        if energy < user.current_month_energy:
            return jsonify({'message': 'Energy goal must be greater than or equal to the total energy cost incurred this month.'}), 400

        # Set the energy goal and save the user
        user.energy_goal = energy
        user.save()

        return jsonify({'message': 'Goal set successfully'}), 201

    except ValueError:
        return jsonify({'message': 'Energy goal must be a numeric value.'}), 400

def delete_goal(user_id):
    # Retrieve the user by ID and make sure they are not deleted
    user = User.objects.get(id=user_id, is_deleted=False)
    if not user:
        return jsonify({'message': 'User not found.'}), 404
    
    user.energy_goal = None
    user.save()
    return jsonify({'message': 'Goal deleted successfully'}), 200

def upload_profile_pic(user_id):
    # Retrieve the user by ID and make sure they are not deleted
    user = User.objects.get(id=user_id, is_deleted=False)

    if not user:
        return jsonify({'message': 'User not found.'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file extension'}), 400

    # Generate a unique filename to avoid conflicts
    filename = secure_filename(file.filename)
    # Generates the full file path by appending the UPLOADS_FOLDER and filename together, 
    # ensuring that the correct path is formed regardless of the operating system using (/ or \)
    save_path = os.path.join(UPLOADS_FOLDER, filename)

    # Save the uploaded profile picture file to the file system.
    try:
        file.save(save_path)
        return jsonify({'message': 'Profile picture uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def get_profile_pic(user_id):
    # Retrieve the user by ID and make sure they are not deleted
    user = User.objects.get(id=user_id, is_deleted=False)

    if not user:
        return jsonify({'message': 'User not found.'}), 404
    
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    try:
        file_path = os.path.join(UPLOADS_FOLDER, filename)
        # Guess the mimetype(extension: png, jpg...) of the file based on the file path
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype:
            # If mimetype is available, return the file with the specified mimetype
            return send_file(file_path, mimetype=mimetype)
        else:
            # If mimetype is not available, return the file without specifying a mimetype
            return send_file(file_path)
    except FileNotFoundError:
        return jsonify({'error': 'Profile picture not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500