"""Authenticate with strava via a webserver"""

"""
URLs

/ - homepage with basic info
/signup - authorize user with Strava
/auth - oauth redirect endpoint; exchange code for auth and refresh tokens
"""

from datetime import datetime
import os
import sys

from flask import redirect
import pandas as pd
from stravalib.client import Client
from stravalib.util import limiter

from process_strava import get_token, refresh_token, save_token
from process_strava import strava_clean

# If empty, assume function is running locally
GOOGLE_CLOUD_REGION=os.environ.get('FUNCTION_REGION')

if GOOGLE_CLOUD_REGION:
  HOST='www.bouldertrailschallenge.com'
else:
  #Assume local
  PORT = os.environ.get('PORT')
  if not PORT:
    PORT='8080'

  HOST='127.0.0.1:{}'.format(PORT)

OAUTH_REDIRECT_URL=os.environ.get('OAUTH_REDIRECT_URL')

if not OAUTH_REDIRECT_URL:
  OAUTH_REDIRECT_URL='http://{}/auth'.format(HOST)

def home(request):
  return """Visit {}/signup""".format(HOST)

def signup(request):
  # TODO(nswanberg) find a way to store these in Google Cloud
  client_id, client_secret = open('secrets-chaya.txt').read().strip().split(',')

  client = Client(rate_limiter=limiter.DefaultRateLimiter())
  # ****This only needs to happen once. Once we have the token we can simply refresh ****

  # TODO(nswanberg) store the token in Firebase or equivalent
  path_to_save = os.path.join("access_token.pickle")


  # TODO: Adjust scope - probably only need activity:read_all
  # TODO: move this into a one time event that looks for a key - i presume the tokens will be stored in the DB
  # NOTE - this allows access to a lot of profile info AND private activities. we could scope this back to read all easily
  url = client.authorization_url(client_id=client_id,
         # TODO(nswanberg)
         redirect_uri=OAUTH_REDIRECT_URL,
         scope=[ 'activity:read_all'])
  return redirect(url)

def auth(request):
  client = Client(rate_limiter=limiter.DefaultRateLimiter())
  client_id, client_secret = open('secrets-chaya.txt').read().strip().split(',')

  code = request.args.get('code')
  if not code:
    return 'missing code', 400

  # Once we have this setup we can exchange the code for a token
  # The token I think will need to be stored in a (secure) database for each user.
  # Can combine the two lines below just keeping things separate for now
  path_to_save = os.path.join("access_token.pickle")
  print('getting access token')
  access_token = get_token(client, client_id, client_secret, code=code)
  print('saving token')
  save_token(access_token, path_to_save)
  print('saved token')
  return "saved token"

def retrive(request):
  """Not yet implemented as a cloud function"""
  # Begin Good Times -
  # TODO: this maybe should be a try statement so it can fail gracefully
  # Once we have the token we will need to check that it's current
  if os.path.exists(path_to_save):
      refresh_token(client, client_id, client_secret, token_path_pickle=path_to_save)

  # This workflow is really assuming it's the first time we're doing this
  # In reality i'm guessing we'd be storing data somewhere and would have a
  # Date of last activity. I haven't built out that functionality yet so
  # let's hold on that for now and just get this going first.
  athlete_info = client.get_athlete()

  print("Hey there {}, how ya doin on this fine day? Im gonna grab your"
        "\nStrava activities next starting from Dec 1, 2020. You hold on now, "
        "\n ya hear?!".format(athlete_info.firstname))

  # Grab activities and turn into df
  print("Be patient - this may take a minute")
  # TODO: Add time range limit to reduce data download
  all_activities = strava_clean.get_activities(client)

  # Only grab runs, walks and hikes
  act_types = ["Run", "Hike", "Walk"]
  all_runs_hikes = all_activities[all_activities.type.isin(act_types)]

  strava_clean.get_act_gps(client, all_runs_hikes, athlete_info)

  # # Next, grab all spatial data
  # # TODO: We may not need distance or time?
  # types = ['time', 'distance', 'latlng']
  #
  # print("Next I will get your run GPS data.")
  # gdf_list = []
  # for i, act in enumerate(all_runs_hikes["activity_id"].values):
  #         # TODO: Turn this into a small helper
  #         act_data = client.get_activity_streams(act,
  #                                                types=types)
  #         # print(act)
  #         # Some activities have no information associated with them
  #         if act_data:
  #             try:
  #                 gdf_list.append([act,
  #                                  act_data["latlng"].data])
  #             except KeyError:
  #                 # some activities have no gps data like swimming and short activities
  #                 print(
  #                     "LatLon is missing from activity {}. Moving to next activity".format(act))
  #
  # print("You have made {} requests. Strava limits requests to 600 every 15 mins".format(i))
  # print(datetime.now())
  # act_gps_df = pd.DataFrame(gdf_list,
  #                           columns=["activity_id", "xy"])
  # print("Next, I'll export your hiking & running GPS data. Hold on".format(i))
  #
  # gps_data_path = athlete_info.firstname + "_gps_data.csv"
  # act_gps_df.to_csv(gps_data_path)
  # print("I've saved a file called {} for you. ".format(gps_data_path))



