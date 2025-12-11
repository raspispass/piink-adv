from PIL import ExifTags
import os,random
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import json
from PIL import ImageDraw,Image,ImageOps 
from wtforms import SubmitField, FileField, RadioField, BooleanField, DecimalField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_bootstrap import Bootstrap5
from wtforms.validators import InputRequired
import glob
from inky.auto import auto

## Debugging
DEBUG = False

## Initialization
allowed_extensions = {'.png', '.jpg', '.jpeg','.webp'}
path_script = os.path.dirname(os.path.dirname(__file__))
path_upload = os.path.join(path_script,"img")
if not os.path.exists(path_upload):
   os.makedirs(path_upload)
settings_file = os.path.join(path_script,"config/settings.json")
if not DEBUG:
   inky_display = auto()

## Init Flask
app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False
bootstrap = Bootstrap5(app)

## Helpers
def getRandomImg():
    # get random file in upload folder
    pattern=path_upload + "/*"
    files = list(filter(os.path.isfile, glob.glob(pattern)))
    # select a random file
    img_displayed = random.choice(files)
    path_img_displayed = os.path.join(path_upload,img_displayed)
    return path_img_displayed

def getRecentImg():
    # get last modified file in upload folder
    pattern=path_upload + "/*"
    files = list(filter(os.path.isfile, glob.glob(pattern)))
    # sort by modified time
    files.sort(key=lambda x: os.path.getmtime(x))
    # get last item in list
    img_displayed = files[-1]
    path_img_displayed = os.path.join(path_upload,img_displayed)
    return path_img_displayed

## Forms
class UploadForm(FlaskForm):
    # support cURL 'curl -X POST -F "file=@image.png" piink.local'
    file = FileField(validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'webp', 'gif', 'png'], 'Only images')])
    submit_upload = SubmitField('Upload image to PiInk')
class RebootForm(FlaskForm):
    submit_reboot = SubmitField('Reboot')
class ShutdownForm(FlaskForm):
    submit_shutdown = SubmitField('Shutdown')
class RotateForm(FlaskForm):
    submit_rotate_left = SubmitField("←")
    submit_rotate_right = SubmitField("→")
    submit_rotate_updown = SubmitField("↑↓")
class GhostingForm(FlaskForm):
    submit_ghosting = SubmitField('Clear ghosting')
class SaveSettingsForm(FlaskForm):
    orientation = RadioField('Choose display orientation:', validators=[InputRequired(message=None)], choices=[ ('horizontal', 'Horizontal (landscape)'), ('vertical', 'Vertical (portrait)')])
    aspratio = BooleanField('Adjust aspect ratio')
    zoom = BooleanField('Activate/deactivate zoom')
    auto_img_randomize = BooleanField('Display random image after PiInk restart')
    checkmail = BooleanField('Check mails on reboot (new images prioritized over random image display function)')
    reboot_interval = DecimalField('Reboot interval (in seconds) - 1 hour: 3600, 1 day: 86400', places=0)
    reboot_active = BooleanField('Activate or deactivate automatic shutdown and reboot')
    submit_save = SubmitField('Save settings')

## Webserver functions
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    # Load settings from config/settings.json
    settings = loadSettings()

    # Forms
    uploadForm = UploadForm()
    rebootForm= RebootForm()
    shutdownForm = ShutdownForm()
    rotateForm = RotateForm()
    ghostingForm = GhostingForm()
    saveSettingsForm = SaveSettingsForm(orientation=settings['orientation'], aspratio=settings['adjustAspectRatio'], zoom=settings['zoom'], auto_img_randomize=settings['auto_img_randomize'], checkmail=settings['checkmail'], reboot_interval=settings['reboot_interval'], reboot_active=settings['reboot_active'])

    # Message
    message = ""
 
    # Upload
    if uploadForm.file.data and uploadForm.validate_on_submit():
        f = uploadForm.file.data
        filename = secure_filename(f.filename)
        f.save(os.path.join(path_upload, filename))
        filename = os.path.join(path_upload, filename)

        #update the eink display
        updateEink(filename,settings)
        message = "File uploaded successfully"
        return render_template('main.html', uploadForm=uploadForm, rebootForm=rebootForm, shutdownForm=shutdownForm, rotateForm=rotateForm, ghostingForm=ghostingForm, saveSettingsForm=saveSettingsForm, message=message)

    # Reboot
    if rebootForm.submit_reboot.data and rebootForm.validate_on_submit():
        message = "Rebooting ..."
        os.system("sudo reboot")

    # Shutdown
    if shutdownForm.submit_shutdown.data and shutdownForm.validate_on_submit():
        message = "Shutting down system ..."
        os.system("sudo shutdown")

    # Rotate clockwise
    if rotateForm.submit_rotate_left.data and rotateForm.validate_on_submit():
        rotateImage(90, settings)
    if rotateForm.submit_rotate_right.data and rotateForm.validate_on_submit():
        rotateImage(-90, settings)
    if rotateForm.submit_rotate_updown.data and rotateForm.validate_on_submit():
        rotateImage(180, settings)

    # Ghosting clears
    if ghostingForm.submit_ghosting.data and ghostingForm.validate_on_submit():
        clearScreen()

    #save frame settings
    if saveSettingsForm.submit_save.data and saveSettingsForm.validate_on_submit():
        message = "Saved settings"

        orientation = "horizontal"
        aspratio = False
        zoom = False
        auto_img_randomize = False
        checkmail = False
        reboot_interval = 3600
        reboot_active = False

        if saveSettingsForm.orientation.data:
            orientation = request.form["orientation"]
        if saveSettingsForm.aspratio.data:
            aspratio = request.form["aspratio"]
        if saveSettingsForm.zoom.data:
            zoom = request.form["zoom"]
        if saveSettingsForm.auto_img_randomize.data:
            auto_img_randomize = request.form["auto_img_randomize"]
        if saveSettingsForm.checkmail.data:
            checkmail = request.form["checkmail"]
        if saveSettingsForm.reboot_interval.data:
            reboot_interval = int(request.form["reboot_interval"])
        if saveSettingsForm.reboot_active.data:
            reboot_active = request.form["reboot_active"]

        settings = {
            "orientation" : orientation,
            "adjustAspectRatio" : aspratio,
            "zoom" : zoom,
            "auto_img_randomize" : auto_img_randomize,
            "checkmail" : checkmail,
            "reboot_interval" : reboot_interval,
            "reboot_active" : reboot_active,
        }

        saveSettings(settings)
        return render_template('main.html', uploadForm=uploadForm, rebootForm=rebootForm, shutdownForm=shutdownForm, rotateForm=rotateForm, ghostingForm=ghostingForm, saveSettingsForm=saveSettingsForm, message=message)
    return render_template('main.html', uploadForm=uploadForm, rebootForm=rebootForm, shutdownForm=shutdownForm, rotateForm=rotateForm, ghostingForm=ghostingForm, saveSettingsForm=saveSettingsForm, message=message)

## Automatically show (random) image
@app.route('/random', methods=['GET'])
def randomImage():
    # Load settings from config/settings.json
    settings = loadSettings()
    auto_img_randomize=settings['auto_img_randomize']
    if auto_img_randomize == "y":
        updateEink(getRandomImg(),settings)
        return("Random image updated")
    else:
        return("Configuration for random image display is not activated")

def loadSettings():
    # default init settings values
    settings = {
            "orientation" : "horizontal",
            "adjustAspectRatio" : True,
            "zoom" : True,
            "auto_img_randomize" : False,
            "checkmail" : False,
            "reboot_interval" : 3600,
            "reboot_active" : False,
    }

    # try opening existing settings file
    try:
        jsonFile = open(settings_file)
        settings = json.load(jsonFile)
    # write new settings file
    except:
        saveSettings(settings)
        jsonFile = open(settings_file)
        settings = json.load(jsonFile)
    jsonFile.close()
    return settings

def saveSettings(settings):
    with open(settings_file, "w") as f:
        json.dump(settings, f)

def updateEink(filename,settings):
    orientation = settings['orientation']
    aspratio = settings['adjustAspectRatio']
    zoom = settings['zoom']

    with Image.open(os.path.join(path_upload, filename)) as img:
        #do image transforms 
        img = changeOrientation(img, orientation)
        img = adjustAspectRatioAndZoom(img, aspratio, zoom)

        # Display the image
        if not DEBUG:
            inky_display.set_image(img)
            inky_display.show()
        else:
            img.show()

#clear the screen to prevent ghosting
def clearScreen():
    settings = loadSettings()
    img = Image.new(mode="RGB", size=(800, 480),color=(255,255,255))
    clearImage = ImageDraw.Draw(img)
    inky_display.set_image(img)
    inky_display.show()
    updateEink(getRecentImg(),settings)

# Source: https://wolfgang-ziegler.com/blog/ink-display
def changeOrientation(img,orientation):
    # Short version:
    #img = ImageOps.exif_transpose(img)
    # Long version:
    # Check if the image has EXIF data
    if hasattr(img, '_getexif'):
        exif = img._getexif()
        if exif is not None:
            # Look for the EXIF orientation tag
            for tag, orientation_exif in ExifTags.TAGS.items():
                if orientation_exif == 'Orientation':
                    break
            # Check if the orientation tag exists in the EXIF data
            if tag in exif:
                # Get the actual orientation value
                orientation_value = exif[tag]

                # Determine if rotation is needed based on the orientation value
                if orientation_value == 1:
                    # orientation 1: Landscape (correct direction - nothing to do)
                    # No rotation needed (normal orientation)
                    pass
                elif orientation_value == 3:
                    # orientation 3: Landscape (upside down)
                    # Rotate 180 degrees
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    # Rotate 270 degrees
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    # Rotate 90 degrees
                    img = img.rotate(90, expand=True)

    # PiInk orientation
    # change image orientation according to display orientation
    if orientation == "horizontal":
        img = img.rotate(0, expand=True)
    elif orientation == "vertical":
        img = img.rotate(90, expand=True)
    return img

def adjustAspectRatioAndZoom(img, aspratio, zoom):
    if aspratio == "y":
        dsp_w = 800
        dsp_h = 480

        ratioWidth = dsp_w / img.width
        ratioHeight = dsp_h / img.height
        if ratioWidth < ratioHeight:
            # It must be fixed by width
            resizedWidth = dsp_w
            resizedHeight = round(ratioWidth * img.height)
        else:
            # Fixed by height
            resizedWidth = round(ratioHeight * img.width)
            resizedHeight = dsp_h
        imgResized = img.resize((resizedWidth, resizedHeight), Image.LANCZOS)
        background = Image.new('RGBA', (dsp_w, dsp_h), (0, 0, 0, 255))

        if zoom == "y":
            img_zoom = ImageOps.fit(
                img,
                (dsp_w, dsp_h),
                method=Image.LANCZOS,
                centering=(0.5, 0.5),
            )
            img = img_zoom
        else:
            #offset image for background and paste the image
            offset = (round((dsp_w - resizedWidth) / 2), round((dsp_h - resizedHeight) / 2))
            background.paste(imgResized, offset)
            img = background
    else:
        img = img.resize((800, 480))
    return img

def deleteImage():
    img_displayed = getRecentImg()
    if os.path.isfile(img_displayed):
        os.remove(img_displayed)
            
def rotateImage(deg, settings):
    settings = loadSettings()
    img_displayed = getRecentImg()

    with Image.open(img_displayed) as img:
        #rotate image by degrees and update
        img = img.rotate(deg, Image.NEAREST,expand=1)
        img = img.save(img_displayed)
        updateEink(img_displayed,settings)

#run button checks on gpio    
if __name__ == '__main__':
    app.secret_key = str(random.randint(100000,999999))
    if not DEBUG:
        app.run(host="0.0.0.0",port=80,debug=True)
    else:
        app.run(host="0.0.0.0",port=8080,debug=True)
