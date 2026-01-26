import streamlit as st
import os
import glob
from src.agents.tutor_agent import TutorAgent
from src.agents.ingestion_agent import IngestionAgent # For Ingest UI
from src.core.config import Config

# Page Config
st.set_page_config(
    page_title="Smart Practice Tutor",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 60px;
        font-size: 18px;
        background-color: #262730;
        color: white;
        border: 1px solid #4B4B4B;
    }
    .stButton>button:hover {
        background-color: #4B4B4B;
        color: white;
        border-color: #646cff;
    }
    .question-card {
        padding: 30px;
        background-color: #1e1e1e;
        border-radius: 15px;
        margin-bottom: 25px;
        border-left: 5px solid #646cff;
        font-size: 22px;
        font-weight: 500;
    }
    .feedback-box {
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
    .success {
        background-color: rgba(76, 175, 80, 0.1);
        border: 1px solid #4CAF50;
        color: #4CAF50;
    }
    .error {
        background-color: rgba(244, 67, 54, 0.1);
        border: 1px solid #F44336;
        color: #F44336;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Navigation & Setup ---
with st.sidebar:
    st.header("📚 Topic Library")
    
    # 1. Topic Scanner
    db_files = glob.glob("data/db/*.json")
    topics = [os.path.basename(f).replace(".json", "") for f in db_files]
    
    if not topics:
        st.warning("No topics found. Please ingest one below.")
    
    selected_topic = st.selectbox("Select Topic", topics, index=0 if topics else None)
    
    st.divider()
    
    # 2. Ingest New
    st.subheader("Ingest New Data")
    new_topic_name = st.text_input("Topic Name (e.g., python_basics)")
    if st.button("🚀 Ingest"):
        if new_topic_name:
            with st.spinner(f"Ingesting '{new_topic_name}'... (This takes time)"):
                try:
                    # Create dummy folder if needed just for demo flow
                    # In real app, user puts file there.
                    path = f"data/uploads/{new_topic_name}"
                    if not os.path.exists(path):
                        os.makedirs(path, exist_ok=True)
                        with open(f"{path}/intro.txt", "w") as f:
                             f.write(f"Introduction to {new_topic_name}")
                    
                    ingest_agent = IngestionAgent()
                    ingest_agent.load_topic(new_topic_name)
                    st.success("Analysis Complete! Refreshing...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

# --- Main Logic: Session Management ---

if "agent" not in st.session_state:
    st.session_state.agent = TutorAgent()
    st.session_state.current_q = None
    st.session_state.feedback = None
    st.session_state.topic_started = False

# Start Session if Topic Changed
if selected_topic and (not st.session_state.topic_started or st.session_state.agent.session.current_topic != selected_topic):
    try:
        st.session_state.agent.start_session("user_stream", selected_topic)
        st.session_state.topic_started = True
        st.session_state.current_q = st.session_state.agent.get_next_question()
        st.session_state.feedback = None
        st.rerun()
    except Exception as e:
        st.error(f"Could not start session: {e}")

# --- UI Render ---

st.title("🧠 Smart Practice Tutor")

if not selected_topic:
    st.info("👈 Select or Ingest a topic to begin.")
    st.stop()

# Progress Bar (Mockup for now, could use session stats)
# progress = len(st.session_state.agent.session.coverage_map.keys()) / 10 # heuristic
# st.progress(progress, text="Mastery Progress")

q = st.session_state.current_q

if not q:
    st.balloons()
    st.success("🎉 Topic Mastered! You have completed all available concepts in this library.")
    if st.button("Restart Topic"):
        st.session_state.topic_started = False
        st.rerun()
    st.stop()

# 1. Breadcrumbs & Question Card
active_node_id = st.session_state.agent.session.active_node_id
active_node = st.session_state.agent.kb.node_map.get(active_node_id)
# Clean path: "python_basics > Variables > Definition" -> "Variables / Definition"
breadcrumb = active_node.path.replace(" > ", "  /  ") if active_node else ""

st.markdown(f"""
<div style="color: #646cff; font-size: 14px; font-weight: 600; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;">
    📍 {breadcrumb}
</div>
<div class="question-card">
    <div style="font-size: 14px; text-transform: uppercase; color: #888; margin-bottom: 10px;">
        {q.difficulty.name} • Streak: {st.session_state.agent.session.node_states[active_node_id].correct_streak} / {Config.TUTOR_MASTERY_STREAK}
    </div>
    {q.content}
</div>
""", unsafe_allow_html=True)

# 2. Options Grid
cols = st.columns(2)
# We need to map buttons to actual options.
# Options list usually [A, B, C, D] or full text. 
# Our schema: options=["A", "B", "C", "D"] usually, but demo had text options. 
# Let's handle both.
for idx, opt in enumerate(q.options):
    col = cols[idx % 2]
    # Button callback
    def submit(o=opt):
        res = st.session_state.agent.submit_answer(q.id, o)
        st.session_state.feedback = res
        # Fetch next immediately? Or wait for 'Next' click?
        # Immediate feedback style
        
    if st.session_state.feedback:
        # Disable buttons if answer submitted
        col.button(opt, key=f"btn_{idx}", disabled=True)
    else:
        col.button(opt, key=f"btn_{idx}", on_click=submit)

# 3. Feedback Processing
if st.session_state.feedback:
    res = st.session_state.feedback
    css_class = "success" if res.is_correct else "error"
    icon = "✅" if res.is_correct else "❌"
    
    st.markdown(f"""
    <div class="feedback-box {css_class}">
        <h3>{icon} { "Correct!" if res.is_correct else "Incorrect" }</h3>
        <p>{res.feedback}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Next Question ➡️", type="primary"):
        st.session_state.feedback = None
        st.session_state.current_q = st.session_state.agent.get_next_question()
        st.rerun()
