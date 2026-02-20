from googleapiclient.discovery import build
import pandas as pd
import streamlit as st
import plotly.express as px

# ----------------------------
# CONFIGURATION
# ----------------------------

API_KEY = "ENTER-YOUR-API-KEY"
CHANNEL_ID = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"  # PewDiePie Channel ID

youtube = build('youtube', 'v3', developerKey=API_KEY)

# ----------------------------
# PAGE SETTINGS
# ----------------------------

st.set_page_config(page_title="YouTube Data Dashboard", layout="wide")

st.title("📊 YouTube Data Dashboard")
st.markdown("Analyze YouTube channel performance using YouTube Data API")

# ----------------------------
# FETCH CHANNEL STATS
# ----------------------------

def get_channel_stats(channel_id):
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    )
    response = request.execute()
    data = response['items'][0]

    return {
        "Channel Name": data['snippet']['title'],
        "Subscribers": int(data['statistics']['subscriberCount']),
        "Views": int(data['statistics']['viewCount']),
        "Total Videos": int(data['statistics']['videoCount']),
        "Uploads Playlist": data['contentDetails']['relatedPlaylists']['uploads']
    }

# ----------------------------
# FETCH VIDEO STATS
# ----------------------------

def get_video_data(playlist_id, max_results):
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=max_results
    )
    response = request.execute()

    video_ids = []
    for item in response['items']:
        video_ids.append(item['snippet']['resourceId']['videoId'])

    video_request = youtube.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids)
    )
    video_response = video_request.execute()

    data = []
    for video in video_response['items']:
        data.append({
            "Title": video['snippet']['title'],
            "Published Date": video['snippet']['publishedAt'][:10],
            "Views": int(video['statistics'].get('viewCount', 0)),
            "Likes": int(video['statistics'].get('likeCount', 0)),
            "Comments": int(video['statistics'].get('commentCount', 0))
        })

    return pd.DataFrame(data)

# ----------------------------
# DISPLAY CHANNEL DATA
# ----------------------------

channel_data = get_channel_stats(CHANNEL_ID)

col1, col2, col3 = st.columns(3)

col1.metric("Subscribers", f"{channel_data['Subscribers']:,}")
col2.metric("Total Views", f"{channel_data['Views']:,}")
col3.metric("Total Videos", f"{channel_data['Total Videos']:,}")

st.divider()

# ----------------------------
# INTERACTIVE VIDEO SECTION
# ----------------------------

st.subheader("🎥 Video Performance Analysis")

num_videos = st.slider("Select number of recent videos", 5, 50, 10)

video_df = get_video_data(channel_data["Uploads Playlist"], num_videos)

# Sort by Views
video_df_sorted = video_df.sort_values(by="Views", ascending=False)

# ----------------------------
# BAR CHART - TOP VIDEOS
# ----------------------------

st.subheader("🔥 Top Videos by Views")

fig_bar = px.bar(
    video_df_sorted,
    x="Title",
    y="Views",
    hover_data=["Likes", "Comments"],
)

fig_bar.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------------
# ENGAGEMENT SCATTER CHART
# ----------------------------

st.subheader("📈 Engagement Analysis")

fig_scatter = px.scatter(
    video_df,
    x="Likes",
    y="Comments",
    size="Views",
    hover_name="Title",
)

st.plotly_chart(fig_scatter, use_container_width=True)

# ----------------------------
# DATA TABLE
# ----------------------------

st.subheader("📄 Video Data Table")

st.dataframe(video_df)

st.download_button(
    "Download Data as CSV",
    video_df.to_csv(index=False),
    "youtube_video_data.csv",
    "text/csv"
)