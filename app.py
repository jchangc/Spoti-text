import pprint
import sys
import json
import datetime
import requests
import spotilib

from twilio.rest import Client
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import spotipy.util as util

## Need to make both of these args ##
username = "1276816718"
playlist_id = "03oGzb072HhmKeoFqOhlP9"
playlist_username = "1276816718"
redirect_uri = 'localhost:/callback'

##################################################
## Don't touch ##
## For Spotify! ##
client_id ='849d454641c048b8bb8bbd15c445e6c4'
client_secret ='b3845facd6be4984a2eca61e1cbf81f9'

## For Twilio ## 
account_sid = 'ACa90e2d207d07442235cd4b04e8ec1d9b'
auth_token = '4ac87485f39038dfe9e786cef45c3f3d'

###################################################

app = Flask(__name__)

@app.route('/')
def homepage():
	return "What's good!"

@app.route('/callback')
def callback():
	return "Callback page."

@app.route('/sms', methods=['POST'])
def sms():
    number = request.form['From']
    message_body = request.form['Body']
    if (message_body.startswith("add:")):
    	search_term = message_body.split(':')[1]

    	## Results
    	song_id = searchTrackName(search_term)[0]
    	song_name = searchTrackName(search_term)[1]

    	addToPlaylist(song_id)
    	resp = MessagingResponse()
    	resp.message('Hello {}, you successfully queued "{}" to the playlist.'.format(number, song_name))
    	return str(resp)

    if (message_body.startswith("playlist change:")):
    	print("PLAYLIST CHANGE")
    	link = message_body.split(':')[1]
    	name = playlistChange(link)
    	resp = MessagingResponse()
    	resp.message('Hello {}, you successfully changed the playlist to {}.'.format(number, name))
    	return str(resp)

    if (message_body.startswith("remove:")):
    	search_term = message_body.split(':')[1]

    	## Results
    	song_id = searchTrackName(search_term)[0]
    	song_name = searchTrackName(search_term)[1]

    	removeFromPlaylist(song_id)
    	resp = MessagingResponse()
    	resp.message('Hello {}, you successfully removed "{}" to the playlist.'.format(number, song_name))
    	return str(resp)

    if (message_body.startswith("tracklist")):
    	tlist = returnTracklist()
    	resp = MessagingResponse()
    	resp.message('Hello {}, here are the tracks: \n \n {}'.format(number, tlist))
    	return str(resp)

    if (message_body.startswith("currently playing")):
    	track = returnCurrentTrack()
    	resp = MessagingResponse()
    	resp.message('Hello {}, the track currently playing is: \n {}'.format(number, track))
    	return str(resp)

    if (message_body.startswith("create new playlist: ")):
    	playlist_name = message_body.split(': ')[1]
    	print(playlist_name)
    	createNewPlaylist(playlist_name)
    	resp = MessagingResponse()
    	resp.message('Hello {}, {} has been created and set as the new playlist.'.format(number, playlist_name))
    	return str(resp)

scope = 'playlist-modify-public user-library-modify user-read-currently-playing'
token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri = 'http://localhost:5000/')

token_dict = {}
token_dict[username] = token

client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)

# ### Functions all here ###

def returnTracklist():
	if token:
		sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)
		sp.trace = False
		tracklist = sp.user_playlist(playlist_username, playlist_id)['tracks']['items']
		track_ids = [e['track']['id'] for e in tracklist]
		track_names = ""

		for song_id in track_ids:
		    artists = sp.track(song_id)['artists']
		    artists_str = ' & '.join(e['name'] for e in artists)
		    name = artists_str + " - " + sp.track(song_id)['name']
		    track_names += (name + "\n" + "\n")
		return track_names

# def exportPlaylist(user_id):
# 	#Need to authenticate first before creating playlist



def removeFromPlaylist(track_id):
	if token:
	    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)
	    sp.trace = False
	    l = []
	    l.append(track_id)
	    results = sp.user_playlist_remove_all_occurrences_of_tracks(username, playlist_id, l)
	    pprint.pprint(results)
	else:
	    print("Can't get token for", username)

def playlistChange(link):
	if token:
		sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)
		sp.trace = False
		user = link.split('/')[1]
		new_playlistID = link.split('/')[3]
		global playlist_id 
		playlist_id = new_playlistID
		global playlist_username
		playlist_username = user

		return sp.user_playlist(user, new_playlistID, 'name')['name']
	else:
	    print("Can't get token for", username)

def createNewPlaylist(name):
	if token:
	    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)
	    sp.trace = False
	    playlist = sp.user_playlist_create(username, name)
	    pprint.pprint(playlist)
	    global playlist_id 
	    playlist_id = playlist['id']
	else:
	    print("Can't get token for", username)

def addToPlaylist(track_id):
	if token:
	    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)
	    sp.trace = False
	    l = []
	    l.append(track_id)
	    results = sp.user_playlist_add_tracks(username, playlist_id, l)
	    pprint.pprint(results)
	else:
	    print("Can't get token for", username)

def searchTrackName(track_name):
	if token:
	    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)
	    sp.trace = False
	    result_unparsed = sp.search(track_name)['tracks']['items'][0]['uri']
	    song_id = result_unparsed.split(':')[2]

	    artists = sp.track(song_id)['artists']
	    artists_str = ' & '.join(e['name'] for e in artists)
	    
	    name = artists_str + " - " + sp.track(song_id)['name']

	    return song_id, name
	else:
	    print("Can't get token for", username)

def returnCurrentTrack():
	headers = {'Authorization': 'Bearer ' + token}    	
	response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers = headers)
	data = json.loads(response.text)
	artists_str = ' & '.join(e['name'] for e in data['item']['artists'])
	return artists_str + " - " + data['item']['name']

if __name__ == '__main__': 
    app.run(use_reloader=True, debug=True)
