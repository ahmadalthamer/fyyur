import os

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode, and enable development enviroment
DEBUG=True
ENV="development"

# Connect to the database
userName = 'postgres'
password = 'Ahmad@123'
SQLALCHEMY_DATABASE_URI = 'postgres://'+userName+':'+password+'@localhost:5432/fyyur'
SQLALCHEMY_TRACK_MODIFICATIONS = True