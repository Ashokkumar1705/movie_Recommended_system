# 🎬 Movie Recommender System (Streamlit + TMDB)

> **Hook line:** *“Netflix-style movie recommendations in a tiny, deployable Streamlit app.”*

Fast, lightweight, and deployment-ready **content‑based** movie recommender that suggests the **Top‑5 similar movies** for any title you pick. Posters are fetched live from **TMDB** and the similarity matrix is shipped as a **compressed** artifact (`similarity.pkl.gz`) so it’s GitHub/Streamlit‑friendly.

---

## 🧩 Problem Statement

Users get overwhelmed by thousands of movie choices. How can we **personalize** the experience and show **relevant** titles instantly without tracking users or collecting ratings?

---

## ✅ Solution Overview

A **content‑based recommendation system** built on movie metadata. We engineer a `tags` feature (genres + keywords + overview, etc.), vectorize it using **TF‑IDF**, and compute **cosine similarity** across movies. For any selected movie, we return the 5 highest‑scoring neighbors.

### 🔧 Tech Stack

* **Python 3.9+**
* **Pandas, NumPy, Scikit‑learn** (TF‑IDF + cosine similarity)
* **Streamlit** for the UI
* **Requests** for TMDB API calls (posters)
* **Pickle + Gzip** to store the precomputed similarity matrix as `similarity.pkl.gz`

### 📦 Data

* `tmdb_5000_movies.csv`
* `tmdb_5000_credits.csv`

> You can build your own `movies.pkl` (with columns at least `title` and `movie_id`) and the compressed `similarity.pkl.gz` following the pipeline below.

---

## 🗂️ Repository Structure

```
.
├─ app.py                     # Streamlit app
├─ movies.pkl                 # Metadata (title, movie_id, tags, ...)
├─ similarity.pkl.gz         # Gzipped cosine-similarity matrix
├─ requirements.txt           # Python deps
├─ Procfile (optional)        # For some PaaS
├─ .streamlit/
│  └─ secrets.toml            # Holds TMDB_API_KEY when deploying to Streamlit Cloud
└─ README.md
```

---

## 🚀 Quickstart (Local)

### 1) Clone & create env

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python -m venv .venv
. .venv/Scripts/activate   # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Add your TMDB API key

Create `.streamlit/secrets.toml` (local works too):

```toml
TMDB_API_KEY = "your_tmdb_api_key_here"
```

> Don’t hardcode API keys in code. Use `st.secrets["TMDB_API_KEY"]` (see code snippet below).

### 4) Run the app

```bash
streamlit run app.py
```

Open the shown local URL in your browser. Search a movie → click **Recommend** → see 5 similar titles + posters.

---

## 🧪 How It Works (Pipeline)

1. **Preprocessing**: load TMDB CSVs, merge metadata, build a `tags` column (genres + keywords + overview cleaned).
2. **Vectorization**: apply **TfidfVectorizer** (min\_df, stopwords, n‑gram tuning optional).
3. **Similarity**: compute cosine similarity matrix (`N x N`).
4. **Persist**: save as `similarity.pkl.gz` (gzip) to keep the file < 100MB for GitHub/Streamlit.
5. **Serve**: Streamlit reads `movies.pkl` + `similarity.pkl.gz`, computes Top‑5 neighbors for the selected title, fetches poster URLs from TMDB by `movie_id` and renders.

### 🔐 Poster Fetching (TMDB)

* Endpoint: `https://api.themoviedb.org/3/movie/{movie_id}`
* Image base: `https://image.tmdb.org/t/p/w500{poster_path}`
* Use retries + small delay to avoid `429` and flaky networks.

---

## 🧩 App Code Highlights

Below is the **core** logic you can use inside `app.py`:

```python
import streamlit as st
import pickle, gzip, time, os
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PLACEHOLDER = "https://via.placeholder.com/500x750?text=No+Image"

# Robust requests session (retries)
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.6, status_forcelist=[429,500,502,503,504], allowed_methods=["GET"])
session.mount("https://", HTTPAdapter(max_retries=retries))

@st.cache_data(show_spinner=False)
def load_data():
    movies = pickle.load(open("movies.pkl", "rb"))
    with gzip.open("similarity.pkl.gz", "rb") as f:
        similarity = pickle.load(f)
    return movies, similarity


def fetch_poster(movie_id: int) -> str:
    time.sleep(0.4)  # be gentle with TMDB
    api_key = st.secrets.get("TMDB_API_KEY") or os.environ.get("TMDB_API_KEY")
    if not api_key:
        return PLACEHOLDER
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}?api_key={api_key}&language=en-US"
        r = session.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        path = data.get("poster_path") or data.get("backdrop_path")
        return ("https://image.tmdb.org/t/p/w500" + path) if path else PLACEHOLDER
    except Exception:
        return PLACEHOLDER


def recommend(movie, movies, similarity):
    idx = movies[movies["title"] == movie].index[0]
    distances = similarity[idx]
    neighbors = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1:6]

    names, posters = [], []
    for i, _ in neighbors:
        names.append(movies.iloc[i].title)
        posters.append(fetch_poster(movies.iloc[i].movie_id))

    # ensure exactly 5 cards
    while len(names) < 5:
        names.append("N/A"); posters.append(PLACEHOLDER)
    return names, posters


# ================= UI =================
st.title("Movie Recommender System")
movies, similarity = load_data()
movie_list = movies["title"].values
selected = st.selectbox("Pick a movie", movie_list)

if st.button("Recommend"):
    names, posters = recommend(selected, movies, similarity)
    cols = st.columns(5)
    for c, n, p in zip(cols, names, posters):
        with c:
            st.caption(n)
            st.image(p, use_container_width=True)
```

---

## ☁️ Deployment (Streamlit Cloud)

1. Push this repo to GitHub.
2. Go to **share.streamlit.io** → **New app** → connect your GitHub repo → select branch and `app.py`.
3. In **Advanced settings → Secrets**, add:

   ```toml
   TMDB_API_KEY = "your_tmdb_api_key_here"
   ```
4. Deploy. First build will cache `movies.pkl` + `similarity.pkl.gz`.

> **Note:** Avoid pushing uncompressed similarity matrices (`>100MB`) to GitHub. Use the provided `.gz` artifact.

---

## 🔧 Building `similarity.pkl.gz` (optional)

If you want to regenerate the model, create a script like `build_similarity.py`:

```python
import pandas as pd
import numpy as np
import pickle, gzip
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1) load and preprocess your CSVs to create a DataFrame `movies`
#    with at least: title, movie_id, tags (str)

movies = pd.read_csv("tmdb_5000_movies.csv")  # merge/clean as needed
# movies = ... (merge credits, build tags)

# 2) vectorize
vec = TfidfVectorizer(stop_words="english", min_df=2)
X = vec.fit_transform(movies["tags"].fillna(""))

# 3) similarity
sim = cosine_similarity(X)

# 4) save artifacts
movies.to_pickle("movies.pkl")
with gzip.open("similarity.pkl.gz", "wb") as f:
    pickle.dump(sim, f)
```

---

## 🧯 Troubleshooting

**1) Some posters don’t load / show intermittently**

* We use retries + timeout + small sleep to reduce `429` or connection resets.
* TMDB might not have a `poster_path` → we fall back to a placeholder image.

**2) GitHub 100MB limit errors**

* Don’t commit raw `similarity.pkl` if it’s >100MB. Use `similarity.pkl.gz`.
* If a large file slipped into history, clean it with `git filter-repo` or start a fresh repo.

**3) Windows line‑ending warnings (CRLF/LF)**

* Safe to ignore, or set `git config core.autocrlf true` (Windows).

**4) Streamlit Cloud secrets**

* If posters are always placeholders, ensure `TMDB_API_KEY` is set in **Secrets**.

---

## 🗺️ Roadmap

* [ ] Hybrid (content + collaborative) recommendations
* [ ] Search-as-you-type, fuzzy matching
* [ ] Cache TMDB poster URLs locally
* [ ] Model cards & evaluation notebook
* [ ] Dockerfile for containerized deploy

---

## 🙌 Acknowledgements

* **TMDB** for posters & metadata (use per their terms).
* Open datasets from the movie recommendation community.

---

## 📄 License

MIT — feel free to use, modify, and share.

---

