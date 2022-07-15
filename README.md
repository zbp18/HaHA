### HaHA (the Happy Humour Assistant chatbot that helps people learn to laugh) web app
#### Notes

The humour detection model code be found in , but this is only provided for reference and will not be needed to run the bot as the humour scores have been pre-computed.

1) Before running the code in this folder, please obtain the model for emotion classification from https://drive.google.com/drive/folders/19uh2aIyxqzS-4LiagBouu6YuPYiOvaDz?usp=sharing 

2) You may need to change the file paths in 'classifiers.py' and 'rule_based_model.py' to your local paths when running locally

3) This chatbot uses the react-chatbot-kit library: https://fredrikoseberg.github.io/react-chatbot-kit-docs/


#### To run the code in this folder locally, after cloning open a terminal window and do:

$ pip3 install virtualenv

$ virtualenv ./HaHA

$ cd ./HaHA

$ source bin/activate

$ cd ./model

$ python3 -m pip install -r requirements.txt

$ set FLASK_APP=flask_backend_with_aws

$ flask db init

$ flask db migrate -m "testDB table"

$ flask db upgrade

$ nano .env   ---->  add DATABASE_URL="sqlite:////YOUR LOCAL PATH TO THE app.db FILE" to the .env file, save and exit

$ flask run


#### To launch the front end, open another terminal tab and do:

$ cd ./HaHA/view

$ npm i

$ npm run start


Once set up, you can run the chatbot by simply executing the following commands in seperate tabs from the run_project directory:
$ ./run_HaHA_backend.bash
$ ./run_HaHA_frontend.bash

