import streamlit as st
import pickle
import pandas as pd
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import gzip
import os
import base64

# convert local image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

#Load the local background.jpg
img_base64 = get_base64_image("back3.jpg")

# Inject CSS to display the image
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.7);
        z-index: 0;
    }}
    h1, h2, h3, h4, h5, h6, p, span, label {{
        color: white !important;
    }}
    .stSelectbox, .stButton>button {{
        background-color: rgba(20, 20, 20, 0.8);
        color: white;
        border-radius: 8px;
        padding: 5px;
    }}
    img {{
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.7);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

PLACEHOLDER = "https://via.placeholder.com/500x750?text=No+Image"

#  API key from Streamlit Secrets
API_KEY = st.secrets["TMDB_API_KEY"]



# Reusable session with retries (stabilizes flaky network)
session = requests.Session()
retries = Retry(
    total=3,              # try up to 3 times
    backoff_factor=0.6,   # 0.6s, 1.2s, 1.8s...
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_poster(movie_id):
    # small delay so 5 rapid calls don't trigger rate-limit
    time.sleep(0.4)
    try:
        url = f'https://api.themoviedb.org/3/movie/{int(movie_id)}?api_key={API_KEY}&language=en-US'
        response = session.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        path = data.get('poster_path') or data.get('backdrop_path')
        return ("https://image.tmdb.org/t/p/w500" + path) if path else PLACEHOLDER
    except Exception:
        return PLACEHOLDER

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_poster = []
    recommended_movies_ids = []

    for i in movies_list:
        # use real TMDB id saved in DataFrame (change 'movie_id' to your column name if different)
        tmdb_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_poster.append(fetch_poster(tmdb_id))
        recommended_movies_ids.append(tmdb_id)


    # guarantee 5 entries even if some posters fail
    while len(recommended_movies) < 5:
        recommended_movies.append("N/A")
        recommended_movies_poster.append(PLACEHOLDER)

    return recommended_movies, recommended_movies_poster, recommended_movies_ids



movies = pickle.load(open('movies.pkl', 'rb'))
movies_list = movies['title'].values

with gzip.open('similarity.pkl.gz', 'rb') as f:
    similarity = pickle.load(f)


st.title('Movie Recommender System')

selected_movie_name = st.selectbox('Enter your favorite movie', movies_list)

if st.button('Recommend'):
    names, posters, ids = recommend(selected_movie_name)


    # beta_columns -> columns
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:

        st.image(posters[0], use_container_width=True)
        st.markdown(
           f"<p style='color:white; text-align:center;'><a href='https://www.themoviedb.org/movie/{ids[0]}' target='_blank' style='color:white; text-decoration:none;'>{names[0]}</a></p>",
             unsafe_allow_html=True
        )

    with col2:
        st.image(posters[1], use_container_width=True)
        st.markdown(
            f"<p style='color:white; text-align:center;'><a href='https://www.themoviedb.org/movie/{ids[1]}' target='_blank' style='color:white; text-decoration:none;'>{names[1]}</a></p>",
             unsafe_allow_html=True
        )

    with col3:
        st.image(posters[2], use_container_width=True)
        st.markdown(
            f"<p style='color:white; text-align:center;'><a href='https://www.themoviedb.org/movie/{ids[2]}' target='_blank' style='color:white; text-decoration:none;'>{names[2]}</a></p>",
              unsafe_allow_html=True
        )

    with col4:
        st.image(posters[3], use_container_width=True)
        st.markdown(
            f"<p style='color:white; text-align:center;'><a href='https://www.themoviedb.org/movie/{ids[3]}' target='_blank' style='color:white; text-decoration:none;'>{names[3]}</a></p>",
              unsafe_allow_html=True
       )

    with col5:
        st.image(posters[4], use_container_width=True)
        st.markdown(
           f"<p style='color:white; text-align:center;'><a href='https://www.themoviedb.org/movie/{ids[4]}' target='_blank' style='color:white; text-decoration:none;'>{names[4]}</a></p>",
              unsafe_allow_html=True
        )

