# app.py — Enhanced Social Media Agent (fixed no-None errors)
import json
import os
import streamlit as st
from datetime import datetime

# Try new OpenAI client
try:
    from openai import OpenAI
    OPENAI_CLIENT_AVAILABLE = True
except Exception:
    OPENAI_CLIENT_AVAILABLE = False

# Load key from Streamlit secrets
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", "").strip()

# ----------------------------
# Local Demo (fallback)
# ----------------------------
def local_demo_generator(platform, content_type, tone, topic, variation_idx=0):
    base = f"{topic} — {tone} style."
    if content_type == "Caption":
        return f"{base} Hook #{variation_idx+1} 🚀 CTA: Learn more! #demo"
    if content_type == "Hashtags":
        return "#AI #Tech #Innovation #Demo"
    if content_type == "Content Ideas":
        return (
            f"1) What is {topic}?\n"
            f"2) 5 Benefits of {topic}\n"
            f"3) How to start with {topic}"
        )
    if content_type == "30-Day Content Plan":
        return "\n".join([
            f"Day {i+1}: Post about {topic} (Theme: {tone})"
            for i in range(30)
        ])
    return "Demo content"

# ----------------------------
# History Helpers
# ----------------------------
HISTORY_PATH = "history.json"

def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history_entry(entry):
    hist = load_history()
    hist.insert(0, entry)
    with open(HISTORY_PATH, "w", encoding="utf8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)

def history_to_csv_str(hist):
    import pandas as pd
    if not hist:
        return ""
    df = pd.DataFrame(hist)
    return df.to_csv(index=False)

# ----------------------------
# Readability Score (safe)
# ----------------------------
def simple_readability(text: str):
    if not text:
        return "-"
    words = text.split()
    if not words:
        return "-"
    sentences = max(1, text.count('.') + text.count('!') + text.count('?'))
    syllables = sum(len([c for c in w if c.lower() in "aeiou"]) for w in words)
    words_per_sentence = len(words) / sentences
    flesch = 206.835 - 1.015 * words_per_sentence - 84.6 * (syllables / max(1, len(words)))
    return round(flesch, 1)

# ----------------------------
# OpenAI usable?
# ----------------------------
USE_OPENAI = False
client = None

if OPENAI_CLIENT_AVAILABLE and OPENAI_KEY.startswith("sk-"):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        USE_OPENAI = True
    except Exception:
        USE_OPENAI = False

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="AI Social Media Agent", layout="centered")
st.title("📱 AI Social Media Agent — Enhanced")

with st.expander("Settings"):
    col1, col2, col3 = st.columns(3)
    with col1:
        platform = st.selectbox("Platform", ["Instagram", "LinkedIn", "YouTube", "Twitter"])
        content_type = st.selectbox(
            "Content Type",
            ["Caption", "Content Ideas", "Hashtags", "30-Day Content Plan"]
        )
    with col2:
        tone = st.selectbox(
            "Tone", ["Professional", "Funny", "Bold", "Friendly", "Inspirational"]
        )
        variations = st.slider("Variations", 1, 5, 1)
    with col3:
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)

topic = st.text_input("Enter your topic (e.g., lifestyle, AI education, fitness)")
generate = st.button("Generate Content")

# ----------------------------
# Generator
# ----------------------------
def generate_single(platform, content_type, tone, topic, idx):
    """
    Returns: (text, error or None)
    Always returns a string (never None)
    """
    if USE_OPENAI and client is not None:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful social media strategist."},
                    {"role": "user", "content": f"Create {content_type} for {platform} about '{topic}' in {tone} tone."}
                ],
                max_tokens=400,
                temperature=temperature
            )

            out = None
            try:
                out = response.choices[0].message["content"]
            except Exception:
                try:
                    out = response.choices[0].message.content
                except Exception:
                    out = None

            if out is None:
                demo = local_demo_generator(platform, content_type, tone, topic, idx)
                return demo, None

            return out, None

        except Exception as e:
            demo = local_demo_generator(platform, content_type, tone, topic, idx)
            return demo, e

    # fallback if no OpenAI key
    return local_demo_generator(platform, content_type, tone, topic, idx), None

# ----------------------------
# Generate Button
# ----------------------------
if generate:
    if topic.strip() == "":
        st.warning("Please enter a topic.")
    else:
        results = []
        first_error = None

        for i in range(variations):
            out, err = generate_single(platform, content_type, tone, topic, i)
            if err and first_error is None:
                first_error = err
            results.append({"variation": i + 1, "text": out})

        if first_error:
            err_txt = str(first_error)
            if "insufficient_quota" in err_txt or "429" in err_txt:
                st.error("OpenAI quota exhausted or rate-limited. Showing demo output.")
            elif "Invalid" in err_txt or "401" in err_txt:
                st.error("Invalid or unauthorized OpenAI key. Showing demo output.")
            else:
                st.error("OpenAI error occurred. Showing demo output.")

        # ----------------------------
        # Display each variation
        # ----------------------------
        for item in results:
            st.markdown(f"### Variation {item['variation']}")
            text = item.get("text") or ""

            st.write(text)
            score = simple_readability(text)
            st.caption(f"Readability score: {score}")

            # safe escaping
            escaped = (
                text.replace("\\", "\\\\")
                    .replace("`", "\\`")
                    .replace("\n", "\\n")
            )

            copy_js = f"""
            <script>
            function copyToClipboard_{item['variation']}() {{
                navigator.clipboard.writeText(`{escaped}`);
                alert('Copied Variation {item['variation']}');
            }}
            </script>
            <button onclick="copyToClipboard_{item['variation']}()">Copy</button>
            """

            st.markdown(copy_js, unsafe_allow_html=True)

            st.download_button(
                "Download .txt",
                data=text,
                file_name=f"{topic}_variation{item['variation']}.txt",
                mime="text/plain"
            )
            st.markdown("---")

        # ----------------------------
        # Save History
        # ----------------------------
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "platform": platform,
            "content_type": content_type,
            "tone": tone,
            "topic": topic,
            "variations": results,
        }
        save_history_entry(entry)
        st.success("Saved to history successfully.")

# ----------------------------
# History Section
# ----------------------------
st.subheader("📜 History")
hist = load_history()

if hist:
    import pandas as pd
    preview_rows = []
    for h in hist:
        first_text = h["variations"][0]["text"] if h.get("variations") else ""
        preview_rows.append({
            "timestamp": h.get("timestamp"),
            "topic": h.get("topic"),
            "platform": h.get("platform"),
            "type": h.get("content_type"),
            "preview": first_text[:100] + "..." if len(first_text) > 100 else first_text,
        })

    df = pd.DataFrame(preview_rows)
    st.dataframe(df)

    csv_data = history_to_csv_str(hist)
    st.download_button("Download history (CSV)", csv_data, "history.csv", "text/csv")
    st.download_button(
        "Download history (JSON)",
        json.dumps(hist, ensure_ascii=False, indent=2),
        "history.json",
        "application/json"
    )
else:
    st.info("No history yet. Generate content to save.")
