import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv


def create_spotify_client():
    """Create and return an authenticated Spotify client using Authorization Code flow."""
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
            'user-read-email'  # Added as now required by Spotify
        ]),
        show_dialog=True
    )

    return spotipy.Spotify(auth_manager=auth_manager)


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

        # Get recommendations using artist and track seeds
        seed_artists = [input_track['artists'][0]['id']]
        recommendations = sp.recommendations(
            seed_tracks=[input_track_id],
            seed_artists=seed_artists,
            limit=n_recommendations
        )

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
        if e.http_status == 403:
            return "Access denied. Please check your Spotify Developer Dashboard for API access requirements."
        return f"Spotify API error: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


def main():
    """Main function with improved error handling."""
    print("Spotify Song Similarity Finder")
    print("-" * 40)

    try:
        sp = create_spotify_client()
        print("Successfully connected to Spotify!")

        track_name = input("Enter the song name: ").strip()
        artist_name = input("Enter the artist's name: ").strip()
        n_recommendations = min(max(int(input("How many similar songs do you want (1-10)? ")), 1), 10)

        print("\nFinding similar songs...")
        results = find_similar_songs(sp, track_name, artist_name, n_recommendations)

        if isinstance(results, pd.DataFrame):
            print("\nRecommended Songs:")
            print(results.to_string(index=False))
        else:
            print(f"\nError: {results}")

    except ValueError:
        print("Please enter a valid number for recommendations.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()