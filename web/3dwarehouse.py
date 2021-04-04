from flask import Flask, render_template, request, session, url_for, redirect, send_from_directory, jsonify
import pymysql.cursors
import os
import collections
from werkzeug.utils import secure_filename

#Initialize the app from Flask
app = Flask(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))
SCRIPT_FOLDER = dir_path + '/scripts'
# UPLOAD_FOLDER = dir_path + '/photos'
UPLOAD_FOLDER = "/data2/ABC2/data_raw_clustering/gif_and_obj/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SCRIPT_FOLDER'] = SCRIPT_FOLDER
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'obj'])
MODEL_DICTIONARY = collections.defaultdict()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='ycl',
                       password="thisisycl",
                       db='3dwarehouse',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'GET':
        message = {'Greetings':'Hello from python'}
        return jsonify(message)

    if request.method == 'POST':
        print(request.get_json())
        return 'Success', 200

@app.route('/')
def hello():
    # return render_template('3d.html',filename = "23.obj")

    query = "SELECT * FROM Photo"
    cursor = conn.cursor()
    cursor.execute(query)
    models = cursor.fetchall()
    cursor.close()
    for model in models:
        MODEL_DICTIONARY[str(model['pID'])] = (model['photoName'],model['modelName'])
    # print(MODEL_DICTIONARY)
    return render_template('test.html')
    return render_template('tree.html',models=models)

    return render_template('index.html')

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    email= request.form['email']
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person(username,password,email) VALUES(%s,%s,%s)'
        cursor.execute(ins, (username, password,email))
        conn.commit()
        cursor.close()
        return render_template('index.html')


# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        session['password'] = password
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)


@app.route('/home', methods=['GET', 'POST'])
def home():
    username = session['username']
    query = "SELECT * FROM Photo"
    cursor = conn.cursor()
    cursor.execute(query)
    models = cursor.fetchall()
    cursor.close()
    # print(photos)
    if request.method == 'POST':
        # check if the post request has the file part
        # print(request.files)
        if 'photo' not in request.files or 'model' not in request.files:
            print('No file part')
            return redirect(request.url)
        photo = request.files['photo']
        model = request.files['model']
        # if user does not select file, browser also
        # submit a empty part without filename
        if photo.filename == '' or model.filename == '':
            print('No selected file')
            return redirect(request.url)
        if photo and allowed_file(photo.filename) and model and allowed_file(model.filename):
            photo_extension = photo.filename.rsplit('.', 1)[1]
            model_extension = model.filename.rsplit('.', 1)[1]

            ########get pid###########
            cursor = conn.cursor()
            query="SELECT MAX(pID) FROM PHOTO"
            cursor.execute(query)
            pre = cursor.fetchone()['MAX(pID)']
            if pre is None: pid = 0
            else: pid = int(pre) + 1

            ########save photo and model in the static folder######
            # filename = secure_filename(file.filename)
            photoName = str(pid)+'.'+photo_extension
            modelName = str(pid)+'.'+model_extension 
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], photoName)
            photo.save(filepath)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], modelName)
            model.save(filepath)


            query = 'INSERT INTO Photo (pId, username, photoName, modelName) VALUES(%s, %s, %s, %s)'
            cursor.execute(query, (pid, username, photoName, modelName))
            conn.commit()
            cursor.close()
            # redirect(url_for('uploaded_file', photoName=photoName))
            # redirect(url_for('uploaded_model', modelName=modelName))
            return redirect(url_for('home', username=username, models=models))
    return render_template('home.html', username=username, models=models)


# @app.route('/uploads/<photoName>')
# def uploaded_photo(photoName):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],photoName)

@app.route('/uploads/photo/<id>')
def uploaded_photo(id):
    directory = (8-len(id))*'0'+id
    curdir = os.path.join(app.config["UPLOAD_FOLDER"],directory)
    photoName = MODEL_DICTIONARY[id][0]
    return send_from_directory(curdir,photoName)


@app.route('/uploads/model/<id>')
def uploaded_model(id):
    directory = (8-len(id))*'0'+id
    curdir = os.path.join(app.config["UPLOAD_FOLDER"],directory)
    modelName = MODEL_DICTIONARY[id][1]
    print(modelName)
    return send_from_directory(curdir,modelName)


@app.route('/models/<id>')
def model_display(id):
    # send_from_directory(app.config['UPLOAD_FOLDER'],modelName)
    return render_template('3d.html',id=id)
    # return redirect(url_for('3d',modelName=modelName))

@app.route('/scripts/<script>')
def added_script(script):
    return send_from_directory(app.config['SCRIPT_FOLDER'],script)

def change_data(photoID):
    query = "SELECT * FROM Photo WHERE pID=%s"
    cursor = conn.cursor()
    cursor.execute(query,(photoID))
    root = cursor.fetchone()
    print(root)

    query = "SELECT * FROM Photo ORDER BY RAND() LIMIT 9"
    cursor.execute(query)
    children = cursor.fetchall()

    query = "SELECT * FROM Photo ORDER BY RAND() LIMIT 27"
    cursor.execute(query)
    grandchildren = cursor.fetchall()
    cursor.close()

    data = {
    "svg":
            '<g class="centerPerson"><a href="/models/'+str(root['pID'])+'"><path d="M38.9,40h-79.4c-21.2,0-38.3-17.2-38.3-38.3v0c0-21.2,17.2-38.3,38.3-38.3h79.4c21.2,0,38.3,17.2,38.3,38.3v0C77.2,22.8,60,40,38.9,40z"/><g style="clip-path: circle(30px at 50% 50%);"><rect x="-73" y="-38" width="66" height="80" style="background-color: #586577;"/><image style="overflow:visible;" x="-73" y="-38" width="66" height="80" xlink:href="/uploads/photo/'+str(root['pID'])+'"></image></g><text dominant-baseline="central">Car1</text></a></g>',
        "children": [
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[0]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[0]['pID'])+'"></image></g><text>Car2</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car3</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car4</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car5</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[1]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[1]['pID'])+'"></image></g><text>Car6</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car7</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car8</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car9</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[2]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[2]['pID'])+'"></image></g><text>Car10</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car11</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car12</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car13</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[3]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[3]['pID'])+'"></image></g><text>Car14</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car15</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car16</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car17</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[4]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[4]['pID'])+'"></image></g><text>Car18</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car19</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car20</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car21</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[5]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[5]['pID'])+'"></image></g><text>Car22</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car23</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car24</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car25</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[6]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[6]['pID'])+'"></image></g><text>Car26</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car27</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car28</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car29</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[7]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[7]['pID'])+'"></image></g><text>Car30</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car31</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car32</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car33</text></g>',
                        "children": [],
                    },
                ],
            },
            {
                "svg":
                    '<g class="relativePerson"><a href="/tree/'+str(children[8]['pID'])+'"><path d="M28,26h-57.4c-15.3,0-27.7-12.4-27.7-27.7v0c0-15.3,12.4-27.7,27.7-27.7h57.4c15.3,0,27.7,12.4,27.7,27.7v0C55.7,13.6,43.3,26,28,26z"/><g style="clip-path: circle(22px at 50% 50%);"><rect x="-56" y="-32" width="52" height="60" style="background-color: #586577;"/><image style="overflow:visible;" x="-56" y="-32" width="52" height="60" xlink:href="/uploads/photo/'+str(children[8]['pID'])+'"></image></g><text>Car34</text></a></g>',
                "children": [
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car35</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car36</text></g>',
                        "children": [],
                    },
                    {
                        "svg":
                            '<g class="otherPerson"><path d="M19.5,17h-38c-9.6,0-17.5-7.9-17.5-17.5v0c0-9.6,7.9-17.5,17.5-17.5h38c9.6,0,17.5,7.9,17.5,17.5v0C37,9.1,29.1,17,19.5,17z"/><text dominant-baseline="central">Car37</text></g>',
                        "children": [],
                    },
                ],
            },
        ],}
    return data


@app.route('/getdata/<photoID>')
def data_get(photoID):
    print("data_get:"+photoID)
    return jsonify(change_data(photoID))

@app.route('/neighbors/<photoID>')
def get_neighbor(photoID):
    query = "SELECT * FROM Photo WHERE pID=%s"
    cursor = conn.cursor()
    cursor.execute(query,(photoID))
    neighbors = []
    neighbors.append(cursor.fetchone())

    query = "SELECT * FROM Photo ORDER BY RAND() LIMIT 9"
    cursor.execute(query)
    children = cursor.fetchall()
    neighbors.extend(children)
    cursor.close()
    return jsonify(neighbors)
    

@app.route('/tree/<photoID>')
def displayed_tree(photoID):
    print("displayed_tree"+photoID)
    return render_template('tree.html',index = photoID)

@app.route('/xydata')
def xy_data():
    # import random

    query = "SELECT * FROM Photo"
    cursor = conn.cursor()
    cursor.execute(query)
    models = cursor.fetchall()
    cursor.close()
    data = []
    for element in models:
        data.append({
            'x': element['x'],
            'y': element['y'],
            'img': "/uploads/photo/"+str(element['pID']),
            'link': "/models/"+str(element['pID']),
        })
    return jsonify(data)


app.secret_key = 'some key that you will never guess'



#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

print("hello world")