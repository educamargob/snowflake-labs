# Coffee Menu Expert — starting app for Lab 9 (§10).
# You will ENHANCE this app with CoCo. To start over, restore from coffee_kiosk_original.py.
import os
import streamlit as st

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))
session = conn.session()
user = session.get_current_user().strip('"')
my_db = user + "_DB"

st.title("☕ Coffee Menu Expert")
st.caption("Ask any question about our coffee menu")

question = st.text_input("Your question:", placeholder="e.g. Which drink has the most caffeine?")

if question:
    with st.spinner("Thinking..."):
        try:
            kb_content = session.sql(
                f"SELECT LISTAGG(content, '\\n---\\n') WITHIN GROUP (ORDER BY drink_id) FROM {my_db}.RAW.COFFEE_KNOWLEDGE_BASE"
            ).collect()[0][0]

            prompt = (
                "You are a friendly coffee shop assistant. "
                "Answer only using the knowledge base below. "
                "Keep answers short — 2 to 4 sentences for simple questions, a brief paragraph for complex ones. "
                "Use a natural, conversational tone. Do NOT use bullet lists, numbered lists, headers, or markdown formatting. "
                "If the knowledge base does not contain the answer, say you don't have that information.\n\n"
                "KNOWLEDGE BASE:\n" + kb_content + "\n\n"
                "QUESTION: " + question
            )

            result = session.sql(
                "SELECT AI_COMPLETE('llama3.1-70b', ?) AS answer",
                params=[prompt]
            ).collect()[0][0].strip('"').replace('\\n', '\n')

            st.markdown("### Answer")
            st.markdown(result)
        except Exception as e:
            st.error(f"Query failed: {e}")
