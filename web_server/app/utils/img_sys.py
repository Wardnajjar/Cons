#list of extensions of imgs the user can upload
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
#path to where the uploaded images should be saved
UPLOADS_FOLDER = 'uploads/images/'

#function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS