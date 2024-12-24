from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os
from seam_carving import SeamCarver
from PIL import Image  # Import Pillow to handle image operations


# Flask App Configuration
app = Flask(__name__)
UPLOAD_FOLDER = './static/uploads'
RESULT_FOLDER = './static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Ensure upload and result directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Allowed file check
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form inputs
        file = request.files.get('image')
        width = request.form.get('width')
        height = request.form.get('height')
        mask_file = request.files.get('mask')
        mode = request.form.get('mode')  # Either "resize" or "object_removal"

        # Validate inputs
        if not file or not allowed_file(file.filename):
            return render_template('index.html', error="Please upload a valid image file (PNG, JPG, JPEG).")

        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)
        # Open the image using Pillow to get its width and height
        with Image.open(image_path) as img:
            img_width, img_height = img.size


        # Check if resizing mode is selected
        if mode == "resize":
            if not width or not height:
                return render_template('index.html', error="Width and height are required for resizing.")
            try:
                width = int(width)
                height = int(height)
            except ValueError:
                return render_template('index.html', error="Width and height must be numeric values.")

            try:
                result_filename = f"resized_{filename}"
                result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)

                carver = SeamCarver(image_path, height, width)
                carver.save_result(result_path)
                with Image.open(result_path) as result_img:
                    result_width, result_height = result_img.size

                return render_template('index.html',
                                       original_image=image_path,
                                       result_image=result_path,
                                       original_size=f"{img_width} x {img_height}",
                                       result_size=f"{result_width} x {result_height}",
                                       message="Image resized successfully.")
            except Exception as e:
                return render_template('index.html', error=f"An error occurred during resizing: {str(e)}")

        # Check if object removal mode is selected
        elif mode == "object_removal":
            if not mask_file or not allowed_file(mask_file.filename):
                return render_template('index.html', error="Please upload a valid mask image file (PNG, JPG, JPEG).")

            mask_filename = secure_filename(mask_file.filename)
            mask_path = os.path.join(app.config['UPLOAD_FOLDER'], mask_filename)
            mask_file.save(mask_path)

            try:
                result_filename = f"object_removed_{filename}"
                result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)

                carver = SeamCarver(image_path, 0, 0, object_mask=mask_path)
                carver.save_result(result_path)
                

                return render_template('index.html',
                                       original_image=image_path,
                                       result_image=result_path,
                                       message="Object removed successfully.")
            except Exception as e:
                return render_template('index.html', error=f"An error occurred during object removal: {str(e)}")

        else:
            return render_template('index.html', error="Invalid operation selected.")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)