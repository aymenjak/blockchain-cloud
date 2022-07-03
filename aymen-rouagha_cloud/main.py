import pyrebase
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for,session,jsonify
import datetime
import requests
config = {
  "apiKey": "AIzaSyCdGLAgeuKcN7jeRR3FQlrvZQBl31jKcB4",
  "authDomain": "oz-naturals-dz.firebaseapp.com",
  "databaseURL": "https://oz-naturals-dz.firebaseio.com",
  "projectId": "oz-naturals-dz",
  "storageBucket": "oz-naturals-dz.appspot.com",
  "messagingSenderId": "237763791141",
  "appId": "1:237763791141:web:e5d941706790169b35f2cc"
}
import os
#initialize firebase
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
fs = firebase.storage()
from werkzeug.utils import secure_filename
#Initialze person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}

#Login

cloudkey ="30819f300d06092a864886f70d010101050003818d0030818902818100bd81c049aed8a6f05381e194aa09dcf4ce6a39e7a645515ca51bba9a1b7c24b489b20bea86543ff0b7f7dfd00dacb8979e1f13abe4b32bb4543ac810cc88600e00b586e935f078befd3e9f87d8259c8257d6fbb2b5006fe4294845493265cb63121036e9b428f6cdbc098fefbdd1e78a861c1ee818de8e3f17a8893fc0b8f2430203010001"
from collections import OrderedDict
import binascii
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
class Transaction:

    def __init__(self, sender_address, sender_private_key, recipient_address, value,meta_data):
        self.sender_address = sender_address
        self.sender_private_key = sender_private_key
        self.recipient_address = recipient_address
        self.value = value
        self.meta_data=meta_data

    def __getattr__(self, attr):
        return self.data[attr]

    def to_dict(self):
        return OrderedDict({'sender_address': self.sender_address,
                            'recipient_address': self.recipient_address,
                            'amount': self.value,
                            'meta_data':self.meta_data})

    def sign_transaction(self):
        """
        Sign transaction with private key
        """
        private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')



from sqlitedict import SqliteDict
 
class MyClass():
    def __init__(self, param):
        self.param = param
 
def save(key, value, cache_file="cache.sqlite3"):
    try:
        with SqliteDict(cache_file) as mydict:
            mydict[key] = value # Using dict[key] to store
            mydict.commit() # Need to commit() to actually flush the data
    except Exception as ex:
        print("Error during storing data (Possibly unsupported):", ex)
 
def load(key, cache_file="cache.sqlite3"):
    try:
        with SqliteDict(cache_file) as mydict:
            value = mydict[key] # No need to use commit(), since we are only loading data!
        return value
    except Exception as ex:
        print("Error during loading data:", ex)
 
random_gen = Crypto.Random.new().read
private_key = RSA.generate(1024, random_gen)
public_key = private_key.publickey()
response = {
    	'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
		'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    
	}
print("****** user walte ************")
print(response)
obj1 = MyClass(response)




#Initialze flask constructor
app = Flask(__name__)  
@app.route("/")
def login():
    return render_template("login.html")



#Sign up/ Register
@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/logs")
def logs():
    node = "127.0.0.1:8000"
    response = requests.get(f'http://{node}/chain')
    obj2 = load(auth.current_user["localId"])
    logs=[]
    if response.status_code == 200:
        length = response.json()['length']
        chain = response.json()['chain']
        
        for bc in chain:
            if bc["transactions"]!=[]:
                tx=bc["transactions"][0]
                if tx["sender_address"]==obj2.param["public_key"]:
                    logs.append(
                    { 
                    "fname":  tx["meta_data"]['f_name'],
                    "email": person["email"],
                    "statue": tx["meta_data"]['statue'],
                    "timestamp":bc["timestamp"]
                    
                    
                    }
                    )
        print(logs)
    return render_template("user-list.html",logs=logs)




@app.route("/up2", methods=["GET", "POST"])
def upload():
    
    if request.method == 'POST':
      # Get the file from post request
      statue = "upload"
      f = request.files['image']
      # Save the file to ./uploads
      basepath = os.path.dirname(__file__)
      file_path = os.path.join(basepath, 'uploads', secure_filename(f.filename))
      f.save(file_path)
      file_place = "uploads/" + f.filename
      
      obj2 = load(auth.current_user["localId"])
      print("*********** start a tranasaction ************")
      print("whait until file upload ....")
      node = "127.0.0.1:8000"
     
      meta_data={"statue":statue,"f_name":f.filename}
      transaction = Transaction(obj2.param["public_key"], obj2.param["private_key"], cloudkey,"0",meta_data)
      fs.child(auth.current_user["localId"]).child("images").child(f.filename).put(file_place, auth.current_user["idToken"])
      print("*****File Was Uploaded *********")
      
      res = {'transaction': transaction.to_dict(), 'signature': transaction.sign_transaction()}
      print(res)
      nd = requests.get(f'http://{node}/nodes/get')
      response_data = nd.json()
      response = requests.post(f'http://{node}/transactions/new',
                      json=res
                      )
      for n in response_data["nodes"]:
          response = requests.post(f'http://{n}/transactions/new',
                               json=res
                               )
      print("*********** Transcation done ********")
      print(response)
      return redirect(url_for('welcome'))
    return redirect(url_for('welcome'))


@app.route("/delete_file", methods=["POST"])
def delete_file():
    if request.method == 'POST':
      # Get the file from post request
      
      statue = "delete"
      ## reqest file name 
      f_name = request.data.decode("utf-8")
      print("*********** start a tranasaction ************")
      print("whait until file upload ....")
      obj2 = load(auth.current_user["localId"])
      meta_data={"statue":statue,
                 "f_name":f_name}
      transaction = Transaction(obj2.param["public_key"], obj2.param["private_key"], cloudkey, "0",meta_data)
      
      res = {'transaction': transaction.to_dict(), 'signature': transaction.sign_transaction()}
      print(res)
      node = "127.0.0.1:8000"
      response = requests.post(f'http://{node}/transactions/new',
                           json=res
                           )
      print("*********** Transcation done ********")
      print(response)
      return redirect(url_for('welcome')) 
  
@app.route("/view_file", methods=["POST"])
def download_file():
    print("download_file")
    if request.method == 'POST':
      # Get the file from post request
      
      statue = "view file"
      ## reqest file name 
      f_name = request.data.decode("utf-8")
      print("*********** start a tranasaction ************")
      print("whait until file upload ....")
      obj2 = load(auth.current_user["localId"])
      meta_data={"statue":statue,
                 "f_name":f_name}
      transaction = Transaction(obj2.param["public_key"], obj2.param["private_key"], cloudkey, "0",meta_data)
      
      res = {'transaction': transaction.to_dict(), 'signature': transaction.sign_transaction()}
      print(res)
      node = "127.0.0.1:8000"
      response = requests.post(f'http://{node}/transactions/new',
                           json=res
                           )
      print("*********** Transcation done ********")
      print(response)
      return redirect(url_for('welcome')) 
#Welcome page
@app.route("/myfile",methods = ["POST", "GET"])
def welcome():

    if person["is_logged_in"] == True:

        save(auth.current_user["localId"], obj1)
       
        return render_template("page-files.html", email = person["email"], name = person["name"],localID=person["uid"])
    else:
        return redirect(url_for('login'))

#If someone clicks on login, they are redirected to /result
@app.route("/result", methods = ["POST", "GET"])
def result():
    if request.method == "POST":        #Only if data has been posted
        result = request.form           #Get the data
        email = result["email"]
        password = result["pass"]
        try:
            #Try signing in the user with the given information
            user = auth.sign_in_with_email_and_password(email, password)
            #Insert the user data in the global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            #Get the name of the user
            # data = db.child("users").get()
            #print(data)
            #person["name"] = data.val()[person["uid"]]["name"]
            #Redirect to welcome page
            return redirect(url_for('welcome'))
        except:
            #If there is any error, redirect back to login
            return redirect(url_for('login'))
    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('login'))

#If someone clicks on register, they are redirected to /register
@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":        #Only listen to POST
        result = request.form           #Get the data submitted
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        try:
            #Try creating the user account using the provided data
            auth.create_user_with_email_and_password(email, password)
            #Login the user
            user = auth.sign_in_with_email_and_password(email, password)
            #Add data to global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = name
            #Append data to the firebase realtime database
            data = {"name": name, "email": email}
            db.child("users").child(person["uid"]).set(data)
            #Go to welcome page
            return redirect(url_for('welcome'))
        except:
            #If there is any error, redirect to register
            return redirect(url_for('register'))

    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('register'))





######## blochain clinet








if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)
