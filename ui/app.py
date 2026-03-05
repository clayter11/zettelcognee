"""Streamlit UI for ZettelCognee — upload docs, chat with knowledge base."""

import os

import httpx
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")


def get_client() -> httpx.Client:
    """HTTP client with auth token if available."""
    headers = {}
    if "token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return httpx.Client(base_url=API_URL, headers=headers, timeout=60)


def ensure_auth():
    """Auto-login with dev user, register if needed."""
    if "token" in st.session_state:
        return

    client = httpx.Client(base_url=API_URL, timeout=10)

    # Try login first
    resp = client.post("/api/auth/login", data={
        "username": "dev@zettelcognee.com",
        "password": "dev123",
    })
    if resp.status_code == 200:
        st.session_state.token = resp.json()["access_token"]
        return

    # Register dev user
    resp = client.post("/api/auth/register", json={
        "email": "dev@zettelcognee.com",
        "password": "dev123",
        "full_name": "Dev User",
    })
    if resp.status_code == 201:
        resp = client.post("/api/auth/login", data={
            "username": "dev@zettelcognee.com",
            "password": "dev123",
        })
        st.session_state.token = resp.json()["access_token"]


# --- Page config ---
st.set_page_config(page_title="ZettelCognee", page_icon="🧠", layout="wide")
st.title("ZettelCognee")
st.caption("Corporate knowledge base — upload documents, ask questions")

# --- Auth ---
try:
    ensure_auth()
except httpx.ConnectError:
    st.error("Backend не запущен. Выполните: `make up` или `docker compose up`")
    st.stop()

# --- Sidebar: Upload ---
with st.sidebar:
    st.header("📄 Загрузить документ")
    uploaded = st.file_uploader(
        "PDF, Excel, текст, аудио",
        type=["pdf", "xlsx", "xls", "csv", "txt", "md", "docx", "mp3", "wav", "m4a"],
    )
    if uploaded and st.button("Загрузить и обработать"):
        with st.spinner("Загружаю и обрабатываю через Cognee..."):
            client = get_client()
            resp = client.post(
                "/api/documents/upload",
                files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
            )
            if resp.status_code == 201:
                doc = resp.json()
                if doc["status"] == "ready":
                    st.success(f"✅ {doc['filename']} — обработан")
                elif doc["status"] == "error":
                    st.error(f"❌ Ошибка: {doc.get('error_message', 'unknown')}")
                else:
                    st.info(f"⏳ {doc['filename']} — статус: {doc['status']}")
            else:
                st.error(f"Ошибка загрузки: {resp.text}")

    st.divider()

    # Document list
    st.header("📚 Документы")
    try:
        client = get_client()
        resp = client.get("/api/documents/")
        if resp.status_code == 200:
            docs = resp.json()
            if docs["total"] == 0:
                st.info("Нет документов. Загрузите первый!")
            for doc in docs["items"]:
                status_icon = {"ready": "✅", "processing": "⏳", "error": "❌", "uploaded": "📤"}
                icon = status_icon.get(doc["status"], "📄")
                st.text(f"{icon} {doc['filename']}")
    except Exception:
        pass

# --- Main: Chat ---
st.header("💬 Спросить базу знаний")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Задайте вопрос по документам..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Ищу в графе знаний..."):
            client = get_client()
            resp = client.post("/api/search/", json={
                "query": prompt,
                "mode": "graph",
            })

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    # Format results as readable answer
                    answer_parts = []
                    for r in results:
                        if isinstance(r, dict):
                            answer_parts.append(str(r.get("answer", r)))
                        else:
                            answer_parts.append(str(r))
                    answer = "\n\n".join(answer_parts)
                else:
                    answer = "Ничего не найдено. Попробуйте другой запрос или загрузите больше документов."
                st.markdown(answer)
            else:
                answer = f"Ошибка поиска: {resp.text}"
                st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
