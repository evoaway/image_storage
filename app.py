import uuid
from flask import Flask, render_template, request, flash, redirect, url_for
import os

import utils
from classifier import clip_classify, keras_classify
from flask_mysqldb import MySQL

from utils import move_to_beginning, get_metadata, compress

app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'imagesdb'
mysql = MySQL(app)
id = -1  # temporary solution
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        global id
        name = request.form.get('name')
        password = request.form.get('password')
        cur = mysql.connection.cursor()
        cur.execute('''SELECT * FROM users WHERE name = %s and password = %s''', (name, password))
        data = cur.fetchall()
        cur.close()
        if len(data) != 0:
            id = data[0][0]
            return redirect(url_for('upload_file'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        print(name, password)
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO users (name, password) VALUES (%s, %s)''', (name, password))
        mysql.connection.commit()
        cur.close()
        flash(f'Account created for!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/exit', methods=['GET'])
def exit():
    global id
    id = -1
    return redirect(url_for('login'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    result = None
    filename = None
    labels_input = ''
    if request.method == 'POST':
        labels_input = request.form['labels']
        if 'image' not in request.files:
            result = 'No file part'
        else:
            file = request.files['image']
            # if file.filename == '':
            #     result = 'No selected file'
            if not allowed_file(file.filename):
                result = 'Invalid file type. Only allowed file types: png, jpg, jpeg'
            else:
                os.makedirs(f'static/pictures', exist_ok=True)
                image_path = '%s/%s.jpg' % ('static/pictures', str(uuid.uuid4()))
                file.save(image_path)
                hash_name = utils.calculate_image_hash(image_path)
                new_path = '%s/%s.jpg' % ('static/pictures', hash_name)
                if os.path.exists(new_path):
                    os.remove(image_path)
                else:
                    os.rename(image_path, new_path)
                if labels_input:
                    classes = [label.strip() for label in labels_input.split(',')]
                    result = clip_classify(new_path, classes)
                else:
                    result = keras_classify(new_path)
                cur = mysql.connection.cursor()
                cur.execute('''INSERT INTO images (userid, class, filepath) VALUES (%s, %s, %s)''',
                            (id, result, '../' + new_path))
                mysql.connection.commit()
                cur.close()
    return render_template('upload.html', result=result, filename=filename, labels_input=labels_input)


@app.route('/images', methods=['GET', 'POST'])
def get_all_images():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT distinct class FROM images WHERE userid = %s''', (id,))
    classes_tuple = cur.fetchall()
    classes = ["all"] + [i[0] for i in classes_tuple]
    cur.close()
    if request.method == 'GET' or request.form.get('class') == "all":
        cur = mysql.connection.cursor()
        cur.execute('''SELECT * FROM images WHERE userid = %s''', (id,))
        images = cur.fetchall()
        cur.close()
    else:
        images_class = request.form.get('class')
        classes = move_to_beginning(classes, images_class)
        cur = mysql.connection.cursor()
        cur.execute('''SELECT * FROM images WHERE userid = %s and class = %s''', (id, images_class))
        images = cur.fetchall()
        cur.close()
    return render_template('images.html', images=images, classes=classes)


@app.route('/image/<int:image_id>')
def show_image(image_id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM images WHERE id = %s''', (image_id,))
    image = cur.fetchall()
    cur.close()
    metadata = get_metadata(image[0][3][3:])
    return render_template('image.html', image=image[0], metadata=metadata)


@app.route('/image/<int:image_id>', methods=['POST'])
def compress_image(image_id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM images WHERE id = %s''', (image_id,))
    image = cur.fetchall()
    cur.close()
    quality = request.form.get('quality')
    compressed_image_path = '%s/%s.jpg' % ('static/pictures', str(uuid.uuid4()))
    compress(image[0][3][3:], int(quality), compressed_image_path)
    hash_name = utils.calculate_image_hash(compressed_image_path)
    new_path = '%s/%s.jpg' % ('static/pictures', hash_name)
    if os.path.exists(new_path):
        os.remove(compressed_image_path)
    else:
        os.rename(compressed_image_path, new_path)
    cur = mysql.connection.cursor()
    cur.execute('''UPDATE images SET filepath = %s WHERE id = %s''', ('../' + new_path, image_id,))
    mysql.connection.commit()
    cur.close()
    delete_unnecessary(image[0][3])
    return redirect(url_for('get_all_images'))


@app.route('/delete/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM images WHERE id = %s''', (image_id,))
    image = cur.fetchall()
    cur.close()
    file_path = image[0][3]

    cur = mysql.connection.cursor()
    cur.execute('''DELETE FROM images WHERE id = %s''', (image_id,))
    mysql.connection.commit()
    cur.close()
    delete_unnecessary(file_path)

    return redirect(url_for('get_all_images'))

def delete_unnecessary(path):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM images WHERE filepath = %s''', (path,))
    images = cur.fetchall()
    cur.close()
    print(len(images))
    if len(images) == 0:
        os.remove(path[3:])


if __name__ == '__main__':
    app.run(debug=True)
