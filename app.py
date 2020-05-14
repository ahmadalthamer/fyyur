
#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate # adding migrate module
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db) # start using migrate to build the schema

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(),nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    artist = db.relationship('Artist', backref=db.backref('shows', cascade="all,delete"))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    venue = db.relationship('Venue', backref=db.backref('shows', cascade="all,delete"))
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

# #----------------------------------------------------------------------------#
# # Controllers.
# #----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  data = []

  for venueDetails in Venue.query.distinct(Venue.city).all():
    tmp = {}
    tmp['city'] = venueDetails.city
    tmp['state'] = venueDetails.state
    tmpVenue = []
    for extraDetails in Venue.query.filter_by(city = venueDetails.city).all():
      tmpDetail = {}
      tmpDetail['id'] = extraDetails.id
      tmpDetail['name'] = extraDetails.name
      tmpVenue.append(tmpDetail)
    tmp['venues'] = tmpVenue
    data.append(tmp)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_term=request.form.get('search_term', '')
  response = {}
  data = []

  for result in Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all():
    tmp = {}
    tmp['id'] = result.id
    tmp['name'] = result.name
    data.append(tmp)

  response['count'] = len(data)
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  data = []

  for venueDetails in Venue.query.all():
    tmp = {}
    tmp['id'] = venueDetails.id
    tmp['name'] = venueDetails.name
    tmp['genres'] = venueDetails.genres
    tmp['address'] = venueDetails.address
    tmp['city'] = venueDetails.city
    tmp['state'] = venueDetails.state
    tmp['phone'] = venueDetails.phone
    tmp['website'] = venueDetails.website_link
    tmp['facebook_link'] = venueDetails.facebook_link
    tmp['seeking_talent'] = venueDetails.seeking_talent
    tmp['seeking_description'] = venueDetails.seeking_description
    tmp['image_link'] = venueDetails.image_link

    pastShowsData = []
    tmpQuery =  Show.query.join(Artist).join(Venue).filter(Venue.name==venueDetails.name).filter(Show.date<datetime.now()).all()
    for qur in tmpQuery:
      pastShows = {}
      pastShows['artist_id'] = qur.artist.id
      pastShows['artist_name'] = qur.artist.name
      pastShows['artist_image_link'] = qur.artist.image_link
      pastShows['start_time'] = str(qur.date)
      pastShowsData.append(pastShows)

    tmp['past_shows'] = pastShowsData

    upcomingShowsData = []
    tmpQuery =  Show.query.join(Artist).join(Venue).filter(Venue.name==venueDetails.name).filter(Show.date>datetime.now()).all()
    for qur in tmpQuery:
      upcomingShows = {}
      upcomingShows['artist_id'] = qur.artist.id
      upcomingShows['artist_name'] = qur.artist.name
      upcomingShows['artist_image_link'] = qur.artist.image_link
      upcomingShows['start_time'] = str(qur.date)
      upcomingShowsData.append(upcomingShows)

    tmp['upcoming_shows'] = upcomingShowsData
    tmp['past_shows_count'] = len(pastShowsData)
    tmp['upcoming_shows_count'] = len(upcomingShowsData)
    data.append(tmp)

  data = list(filter(lambda d: d['id'] == venue_id, data))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    venue = Venue()
    venue.name = request.form['name']
    venue.genres = request.form.getlist('genres')
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website_link = request.form['website_link']
    if('seeking_talent' in request.form):
      venue.seeking_talent = True
      venue.seeking_description = request.form['seeking_description']
    else:
      venue.seeking_talent = False

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name']+ ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred, venue could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
 
  try:
    VenueDeleted = Venue.query.filter_by(id=venue_id).first()
    db.session.delete(VenueDeleted)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
    flash('Venue ' + VenueDeleted.name+ ' was successfully deleted! refresh the page to update the list')

  return render_template('pages/venues.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data = []

  for artistDetails in Artist.query.all():
    tmp = {}
    tmp['id'] = artistDetails.id
    tmp['name'] = artistDetails.name
    data.append(tmp)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term=request.form.get('search_term', '')
  response = {}
  data = []

  for result in Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all():
    tmp = {}
    tmp['id'] = result.id
    tmp['name'] = result.name
    data.append(tmp)

  response['count'] = len(data)
  response['data'] = data

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  data = []

  for artistDetails in Artist.query.all():
    tmp = {}
    tmp['id'] = artistDetails.id
    tmp['name'] = artistDetails.name
    tmp['genres'] = artistDetails.genres
    tmp['city'] = artistDetails.city
    tmp['state'] = artistDetails.state
    tmp['phone'] = artistDetails.phone
    tmp['website'] = artistDetails.website_link
    tmp['facebook_link'] = artistDetails.facebook_link
    tmp['seeking_venue'] = artistDetails.seeking_talent
    tmp['seeking_description'] = artistDetails.seeking_description
    tmp['image_link'] = artistDetails.image_link

    pastShowsData = []
    tmpQuery =  Show.query.join(Artist).join(Venue).filter(Artist.name==artistDetails.name).filter(Show.date<datetime.now()).all()
    for qur in tmpQuery:
      pastShows = {}
      pastShows['venue_id'] = qur.venue.id
      pastShows['venue_name'] = qur.venue.name
      pastShows['venue_image_link'] = qur.venue.image_link
      pastShows['start_time'] = str(qur.date)
      pastShowsData.append(pastShows)

    tmp['past_shows'] = pastShowsData

    upcomingShowsData = []
    tmpQuery =  Show.query.join(Artist).join(Venue).filter(Artist.name==artistDetails.name).filter(Show.date>datetime.now()).all()
    for qur in tmpQuery:
      upcomingShows = {}
      upcomingShows['venue_id'] = qur.venue.id
      upcomingShows['venue_name'] = qur.venue.name
      upcomingShows['venue_image_link'] = qur.venue.image_link
      upcomingShows['start_time'] = str(qur.date)
      upcomingShowsData.append(upcomingShows)

    tmp['upcoming_shows'] = upcomingShowsData
    tmp['past_shows_count'] = len(pastShowsData)
    tmp['upcoming_shows_count'] = len(upcomingShowsData)
    data.append(tmp)

  data = list(filter(lambda d: d['id'] == artist_id, data))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).one()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  try:
   artist = Artist.query.filter_by(id=artist_id).one()
   
   for editArtist in request.form:
    if (editArtist == 'seeking_venue'):
      continue
    elif(editArtist == 'genres'):
      artist.genres = request.form.getlist('genres')
    else:
      setattr(artist,editArtist,request.form[editArtist])

    if('seeking_venue' not in request.form):
      artist.seeking_talent = False
      artist.seeking_description = None
    else:
      artist.seeking_talent = True
   
   db.session.commit()
   flash('Artist '+request.form['name']+'has been edited successfully!')

  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).one()

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
   venue = Venue.query.filter_by(id=venue_id).one()
   
   for editVenue in request.form:
    if (editVenue == 'seeking_venue'):
      continue
    elif(editVenue == 'genres'):
      venue.genres = request.form.getlist('genres')
    else:
      setattr(venue,editVenue,request.form[editVenue])

    if('seeking_venue' not in request.form):
      venue.seeking_talent = False
      venue.seeking_description = None
    else:
      venue.seeking_talent = True
   
   db.session.commit()
   flash('Venue '+request.form['name']+'has been edited successfully!')

  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  try:
    artist = Artist()
    artist.name = request.form['name']
    artist.genres = request.form.getlist('genres')
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    
    if('seeking_venue' in request.form):
      artist.seeking_talent = True
      artist.seeking_description = request.form['seeking_description']
    else:
      artist.seeking_talent = False

    print(artist.id,file=sys.stderr)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name']+ ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred, artist could not be listed.')
  finally:
    db.session.close()
 
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []

  for showDetails in Show.query.join(Artist).join(Venue).all():
    tmp = {}
    tmp['venue_id'] = showDetails.venue.id
    tmp['venue_name'] = showDetails.venue.name
    tmp['artist_id'] = showDetails.artist.id
    tmp['artist_name'] =  showDetails.artist.name
    tmp['artist_image_link'] = showDetails.artist.image_link
    tmp['start_time'] = str(showDetails.date)
    data.append(tmp)



  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    show = Show()
    show.artist_id = request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.date = request.form['start_time']

    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('Show was failed to be listed!')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# #----------------------------------------------------------------------------#
# # Launch.
# #----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port)

