import uuid
from flask import Flask, render_template, request, flash, redirect, url_for
import os
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


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        global id
        name = request.form.get('name')
        password = request.form.get('password')
        print(name, password)
        cur = mysql.connection.cursor()
        cur.execute('''SELECT * FROM users WHERE name = %s and password = %s''', (name, password))
        data = cur.fetchall()
        cur.close()
        id = data[0][0]
        print(data, id)
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


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    result = None
    filename = None
    labels_input = ''
    if request.method == 'POST':
        labels_input = request.form['labels']
        if 'file' not in request.files:
            result = 'No file part'
        else:
            file = request.files['file']
            if file.filename == '':
                result = 'No selected file'
            else:
                image_path = 'temp_image.jpg'
                file.save(image_path)
                if labels_input:
                    classes = [label.strip() for label in labels_input.split(',')]
                    result = clip_classify(image_path, classes)
                else:
                    result = keras_classify(image_path)
                os.makedirs(f'static/{result}', exist_ok=True)
                new_path = '%s/%s/%s.jpg' % ('static', result, str(uuid.uuid4()))
                os.rename(image_path, new_path)
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
    classes = [i[0] for i in classes_tuple]
    cur.close()
    if request.method == 'GET':
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
    compress(image[0][3][3:], int(quality))
    return redirect(url_for('get_all_images'))


@app.route('/delete/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM images WHERE id = %s''', (image_id,))
    image = cur.fetchall()
    cur.close()
    os.remove(image[0][3][3:])
    cur = mysql.connection.cursor()
    cur.execute('''DELETE FROM images WHERE id = %s''', (image_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('get_all_images'))


if __name__ == '__main__':
    app.run(debug=True)
