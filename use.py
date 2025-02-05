import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv

def create_spotify_client():
    """Create and return an authenticated Spotify client using Authorization Code flow."""
    try:
        auth_manager = SpotifyOAuth(
            client_id='4e2421de960a40a7a5bf8c0742cc7a31',
            client_secret='3ad014f39cbc4d75b40a869f00fb8488',
            redirect_uri='http://localhost:8888/callback',
            scope=' '.join([
                'user-library-read',
                'user-top-read',
                'playlist-modify-public',
                'playlist-modify-private',
                'user-read-private',
                'user-read-email'
            ]),
            show_dialog=True,
            cache_path='.spotify_cache'  # Add cache path
        )
        
        sp = spotipy.Spotify(auth_manager=auth_manager)
        # Test the connection
        sp.current_user()
        return sp
        
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify authentication error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error creating Spotify client: {str(e)}")
        raise

def get_track_features(sp, track_id):
    """Get audio features for a track with error handling."""
    try:
        features = sp.audio_features([track_id])[0]
        if not features:
            return None
            
        # Only use features that are still reliably available
        relevant_features = [
            'danceability', 'energy', 'loudness', 
            'speechiness', 'acousticness', 'instrumentalness',
            'liveness', 'valence', 'tempo'
        ]
        
        return [features[feat] for feat in relevant_features]
    except Exception as e:
        print(f"Error getting audio features for track {track_id}: {str(e)}")
        return None

def find_similar_songs(sp, track_name, artist_name, n_recommendations=5):
    """Find similar songs using available Spotify API features."""
    try:
        # Verify authentication
        user = sp.current_user()
        print(f"Authenticated as: {user['display_name']}")
        
        # Search for the input track
        results = sp.search(q=f"track:{track_name} artist:{artist_name}", type='track', limit=1)
        
        if not results['tracks']['items']:
            return "Song not found. Please check the track name and artist."
            
        input_track = results['tracks']['items'][0]
        input_track_id = input_track['id']
        
        # Debug information
        print(f"\nDebug Information:")
        print(f"Track ID: {input_track_id}")
        print(f"Artist ID: {input_track['artists'][0]['id']}")
        
        # Get recommendations using artist and track seeds with additional parameters
        seed_artists = [input_track['artists'][0]['id']]
        
        print(f"\nMaking recommendation request with parameters:")
        print(f"seed_tracks: {[input_track_id]}")
        print(f"seed_artists: {seed_artists}")
        print(f"limit: {n_recommendations}")
        print(f"market: US")
        
        recommendations = sp.recommendations(
            seed_tracks=[input_track_id],
            seed_artists=seed_artists,
            limit=n_recommendations,
            market='US',  # Add market parameter
            min_popularity=20,  # Add minimum popularity
            max_popularity=100  # Add maximum popularity
        )
        
        if not recommendations['tracks']:
            return "No recommendations found for this track."
        
        # Format results
        similar_tracks = []
        for track in recommendations['tracks']:
            preview_url = track.get('preview_url', 'Not available')
            track_info = {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'popularity': track['popularity'],
                'preview_url': preview_url,
                'spotify_url': track['external_urls']['spotify']
            }
            similar_tracks.append(track_info)
            
        return pd.DataFrame(similar_tracks)

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            return "API endpoint not found. Please check if the track exists."
        elif e.http_status == 403:
            return "Access denied. Please check your Spotify Developer Dashboard for API access requirements."
        elif e.http_status == 401:
            return "Authentication failed. Please check your credentials or re-authenticate."
        return f"Spotify API error: http status: {e.http_status}, code:{e.code} - {e.msg}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    """Main function with improved error handling."""
    print("Spotify Song Similarity Finder")
    print("-" * 40)
    
    try:
        sp = create_spotify_client()
        print("Successfully connected to Spotify!")
        
        while True:
            try:
                track_name = input("\nEnter the song name: ").strip()
                artist_name = input("Enter the artist's name: ").strip()
                n_recommendations = int(input("How many similar songs do you want (1-10)? "))
                
                if not (1 <= n_recommendations <= 10):
                    print("Please enter a number between 1 and 10.")
                    continue
                
                print("\nFinding similar songs...")
                results = find_similar_songs(sp, track_name, artist_name, n_recommendations)
                
                if isinstance(results, pd.DataFrame):
                    print("\nRecommended Songs:")
                    print(results.to_string(index=False))
                else:
                    print(f"\nError: {results}")
                
                # Ask if user wants to search for another song
                again = input("\nWould you like to search for another song? (y/n): ").lower()
                if again != 'y':
                    break
                    
            except ValueError:
                print("Please enter a valid number for recommendations.")
                continue
            except Exception as e:
                print(f"An error occurred during search: {str(e)}")
                continue
            
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    finally:
        print("\nThank you for using Spotify Song Similarity Finder!")

if __name__ == "__main__":
    main()
