import pickle
import os
import time

from langchain_core.documents import Document

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from dotenv import load_dotenv
from db import (
    init_db,
    create_chat,
    get_chats,
    load_chat_messages,
    save_message,
    delete_chat
)

import streamlit as st

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from sentence_transformers import CrossEncoder



load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


st.set_page_config(
    page_title="CHATBOT",
    page_icon="🤖",
    layout="wide"
)
init_db()
if "chat_id" not in st.session_state:

    chats = get_chats()

    if len(chats) > 0:

        st.session_state.chat_id = chats[0][0]

    else:

        st.session_state.chat_id = create_chat()
# =========================================================
# LOAD EMBEDDINGS
# =========================================================

@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5"
    )
@st.cache_resource
def load_pdf_resources(
    vector_path,
    image_path,
    bm25_path,
    parent_docs_path,
    page_map_path,
    _embeddings
):

    vector_db = FAISS.load_local(
        vector_path,
        _embeddings,
        allow_dangerous_deserialization=True
    )

    image_db = FAISS.load_local(
        image_path,
        _embeddings,
        allow_dangerous_deserialization=True
    )

    with open(
        bm25_path,
        "rb"
    ) as f:

        bm25 = pickle.load(f)

    with open(
        parent_docs_path,
        "rb"
    ) as f:

        parent_docs = pickle.load(f)

    with open(
        page_map_path,
        "rb"
    ) as f:

        page_map = pickle.load(f)

    return (
        vector_db,
        image_db,
        bm25,
        parent_docs,
        page_map
    )
    
# =========================================================
# LOAD LLM
# =========================================================

@st.cache_resource
def load_llm():

    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.1-8b-instant"
    )

@st.cache_resource
def load_reranker():

    return CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )

# =========================================================
# LOAD PDF FILES
# =========================================================

pdf_files = [

    f for f in os.listdir(
        "source_docs"
    )

    if f.endswith(".pdf")
]
DATA_ROOT = "data"

pdf_indexes = [

    d for d in os.listdir(DATA_ROOT)

    if os.path.isdir(
        os.path.join(DATA_ROOT, d)
    )
]
if not pdf_indexes:


    st.error(
        "No indexed PDFs found."
    )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Settings")
st.sidebar.markdown("## Chats")

if st.sidebar.button("➕ New Chat"):

    st.session_state.chat_id = create_chat()

    st.rerun()
chats = get_chats()
st.sidebar.markdown("---")
for chat_id, title in chats:

    if st.sidebar.button(
        f"💬 {title}",
        key=f"chat_{chat_id}"
    ):

        st.session_state.chat_id = chat_id

        st.rerun()
# ===================================
# PDF UPLOAD
# ===================================

uploaded_pdf = st.sidebar.file_uploader(
    "📄 Upload PDF",
    type=["pdf"]
)

process_pdf = st.sidebar.button(
    "⚙️ Process PDF"
)

st.sidebar.markdown("---")

# ===================================
# RETRIEVAL
# ===================================

retrieval_mode = st.sidebar.selectbox(
    "Retrieval Mode",
    [
        "Vector Only",
        "Hybrid",
        "BM25 Only",
    ]
)

selected_pdf = st.sidebar.selectbox(
    "Select PDF",
    pdf_indexes
)
CURRENT_PDF_DIR = os.path.join(
    DATA_ROOT,
    selected_pdf
)

VECTOR_PATH = os.path.join(
    CURRENT_PDF_DIR,
    "db_vector_docling"
)

BM25_PATH = os.path.join(
    CURRENT_PDF_DIR,
    "db_bm25_docling",
    "bm25.pkl"
)

IMAGE_PATH = os.path.join(
    CURRENT_PDF_DIR,
    "db_image_faiss"
)

PARENT_DOCS_PATH = os.path.join(
    CURRENT_PDF_DIR,
    "parent_docs_docling.pkl"
)

PAGE_MAP_PATH = os.path.join(
    CURRENT_PDF_DIR,
    "parent_page_map.pkl"
)
embeddings = load_embeddings()

(
    vector_db,
    image_db,
    bm25_retriever,
    parent_docs,
    parent_page_map
) = load_pdf_resources(
    VECTOR_PATH,
    IMAGE_PATH,
    BM25_PATH,
    PARENT_DOCS_PATH,
    PAGE_MAP_PATH,
    embeddings
)

llm = load_llm()

reranker = load_reranker()

top_k = st.sidebar.slider(
    "Top K Results",
    1,
    10,
    3
)

st.sidebar.markdown("---")

st.sidebar.success("FAISS Active")

st.sidebar.write(
    f"PDFs Indexed: {len(pdf_files)}"
)

if st.sidebar.button(
    "🗑 Clear Chat"
):

    
    delete_chat(st.session_state.chat_id)

    st.session_state.chat_id = create_chat()

    st.rerun()

# =========================================================
# TITLE
# =========================================================

st.title(
    "🤖 Document Assistant"
)

strategy_info = {

    "Vector Only":
        "Dense semantic retrieval using embeddings.",

    "BM25 Only":
        "Keyword-based sparse retrieval.",

    "Hybrid":
        "Combines vector + keyword retrieval.",

}

st.caption(
    strategy_info.get(
        retrieval_mode,
        ""
    )
)
messages = load_chat_messages(st.session_state.chat_id)

for role, content in messages:

    with st.chat_message(role):

        st.markdown(content)

# =========================================================
# QUERY INPUT
# =========================================================

query = st.chat_input(
    "Ask your question"
)

# =========================================================
# SEARCH LOGIC
# =========================================================

if query:
    save_message(
    st.session_state.chat_id, 
    "user",
    query
)

    with st.chat_message("user"):

        st.markdown(query)
    results = []

    retrieval_time = 0

    generation_time = 0

    hyp_doc = None

    with st.spinner(
        "Searching documents..."
    ):

        # =================================================
        # START RETRIEVAL TIMER
        # =================================================

        retrieval_start = time.time()

        # =================================================
        # VECTOR ONLY
        # =================================================

        if retrieval_mode == "Vector Only":

            search_results = vector_db.similarity_search(
                query,
                k=top_k * 2
            )

            for doc in search_results:

               results.append(doc)

       

        # =================================================
        # BM25 ONLY
        # =================================================

        elif retrieval_mode == "BM25 Only":

            if bm25_retriever:

                bm25_docs = bm25_retriever.invoke(
                    query
                )

                for doc in bm25_docs:

                    results.append(doc)

            results = results[:top_k * 2]

      

        # =================================================
        # NORMAL HYBRID
        # =================================================

        else:

            vector_results = []

            bm25_results = []

            search_results = vector_db.similarity_search(
                query,
                k=top_k * 2
            )

            for doc in search_results:

                

                 vector_results.append(doc)

            if bm25_retriever:

                bm25_docs = bm25_retriever.invoke(
                    query
                )

                for doc in bm25_docs:

                    bm25_results.append(doc)

            combined = (
                vector_results
                + bm25_results
            )

            seen = set()

            for doc in combined:

                text = doc.page_content

                if text not in seen:

                    seen.add(text)

                    results.append(doc)

            results = results[:top_k * 2]

        # =================================================
        # STOP RETRIEVAL TIMER
        # =================================================

        retrieval_time = (
            time.time() - retrieval_start
        ) * 1000

    # =====================================================
    # NO RESULTS
    # =====================================================

    if len(results) == 0:

        st.warning(
            """
        I could not find this in the documents.

        Try:
            - simpler keywords
            - selecting another PDF
            - another retrieval mode
        """
        )

        st.stop()

   
    # =====================================================
    # CROSS ENCODER RERANKING
    # =====================================================

    if len(results) > 1:
        pairs = [
            (query, doc.page_content)
            for doc in results
        ]

        scores = reranker.predict(pairs)

        ranked = sorted(
            zip(scores, results),
            key=lambda x: x[0],
            reverse=True,
        )

        results = [doc for _, doc in ranked[:top_k]]
    original_results = results.copy()    
    expanded_results = []
    seen_parents = set()

    for doc in results:

        parent_id = doc.metadata.get(
            "parent_id"
        )

        if not parent_id:
            continue
        try:

            parent_num = int(
                parent_id.replace(
                    "parent_",
                    ""
                )
            )

        except:

            continue

        for offset in [ -1, 0, 1]:

            neighbor_id = (
                f"parent_{parent_num + offset}"
            )

            if (
                neighbor_id in parent_docs
                and neighbor_id not in seen_parents
            ):

                expanded_results.append(

                Document(

                    page_content=
                    parent_docs[
                        neighbor_id
        ],

                    metadata={

                        "parent_id":
                        neighbor_id,

                        "source":
                        doc.metadata.get(
                            "source",
                            ""
                ),

                        "document_type":
                        doc.metadata.get(
                            "document_type",
                     ""
                ),

                        "parser":
                        doc.metadata.get(
                            "parser",
                        ""
                    )

            }

        )

)
                seen_parents.add(
                    neighbor_id
                )

                print(
                    f"Expanded: {neighbor_id}"
                )

    if len(expanded_results) > 0:

        results = expanded_results

    def resolve_page(parent_id):

        if not parent_id:

            return None

        return parent_page_map.get(parent_id)
    
    def should_show_image(query):

        context = query.lower()

        image_triggers = [

       "where",
        "location",
        "locate",
        "show me",
        "identify",
        "which port",
        "which connector",
        "service tag",
        "air vent",
        "battery location"

    ]

        return any(
        trigger in context
        for trigger in image_triggers
    )    
    results = results[:5]

    st.write("Context Chunks:", len(results))
    # BUILD CONTEXT

    context = "\n\n==========\n\n".join(
        doc.page_content for doc in results
    )
    with st.expander("🔍 Retrieved Context"):

        for i, doc in enumerate(results, start=1):

            st.write(f"Chunk {i}")

            st.text(doc.page_content[:3000])
    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are an expert assistant for technical manuals and PDF documents.

Instructions:

1. Answer ONLY using the provided context.
2. Never use outside knowledge.
3. Never infer, estimate, assume, or guess.
4. If the answer is not explicitly stated in the context, respond exactly:

I could not find this in the documents.

5. Related information is NOT the answer.

Example:
Question: What is the battery life?
Context: Battery charging time is 3 hours.

Correct answer:
I could not find this in the documents.

6. If the answer is in a table:
   - Read the entire table.
   - Extract ALL relevant values.
   - Do not stop after finding the first value.

7. If dimensions are requested:
   - Include Height
   - Include Width
   - Include Depth

8. If specifications are requested:
   - Include all matching specifications found.

9. If multiple options or configurations exist:
   - List each option separately.

10. Do not say:
   - "Based on the context"
   - "We can infer"
   - "We can assume"
   - "It is likely"
   - "It might be"

11. If the retrieved context does not directly answer the question, respond exactly:

I could not find this in the documents.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

    # =====================================================
    # GENERATION TIMER
    # =====================================================

    generation_start = time.time()

    with open(
        "debug_context.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(context)

    
    response = llm.invoke(
        prompt
    )

    generation_time = (
        time.time() - generation_start
    ) * 1000

    save_message(
        st.session_state.chat_id,
        "assistant",
        getattr(
            response,
            "content",
            ""
        )
    )

    # =====================================================
    # ANSWER
    # =====================================================

    with st.chat_message("assistant"):

        st.markdown(
            getattr(
                response,
                "content",
                ""
            )
        )

    retrieved_pages = set()

    for doc in results:

        page = resolve_page(
            doc.metadata.get(
                "parent_id"
            )
        )

        if page is not None:
            retrieved_pages.add(
                page
            )

    # ==========================================
    # IMAGE SEARCH
    # ==========================================

    st.write("## Related Images")

    if query and query.strip() and should_show_image(context):

        image_results = image_db.similarity_search_with_score(
            query,
            k=5
        )

        filtered_images = []

        for doc, score in image_results:

            if score < 0.5:
                filtered_images.append((doc, score))

        if len(filtered_images) > 0:

            pairs = [
                (query, doc.page_content)
                for doc, _ in filtered_images
            ]

            rerank_scores = reranker.predict(pairs)

            ranked_images = sorted(
                zip(rerank_scores, filtered_images),
                key=lambda x: x[0],
                reverse=True
            )

            _, best_image = ranked_images[0]
            doc, faiss_score = best_image

            image_path = doc.metadata.get("image_path")
            caption = doc.metadata.get("caption", "")

            if image_path:

                st.image(
                    image_path,
                    caption=caption,
                    width=800
                )

                st.write(
                    f"Image Score: {faiss_score:.4f}"
                )

            else:

                st.info(
                    "No image path found."
                )

        else:

            st.write(
                "No related images found."
            )

    else:

        st.write(
            "No image required for this answer."
        )

    # ================================================
    # METRICS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Chunks Retrieved",
            len(results)
        )

    with col2:
        st.metric(
            "Retrieval Latency",
            f"{retrieval_time:.2f} ms"
        )

    with col3:
        st.metric(
            "Generation Latency",
            f"{generation_time:.2f} ms"
        )

    # =====================================================
    # SOURCES
    # =====================================================

    st.write("## Sources")
    if len(results) > 0:

        first_source = results[0].metadata.get(
        "source",
        ""
    )

    encoded_name = os.path.basename(
        first_source
    ).replace(
        " ",
        "%20"
    )

    full_pdf_url = (
        f"http://localhost:8000/"
        f"{encoded_name}"
    )

    st.link_button(
        "📖 Open Full Manual",
        full_pdf_url
    )
    shown = set()

    for idx, doc in enumerate(results, start=1):
        source_path = doc.metadata.get(
            "source",
            "Unknown"
        )

        source_name = os.path.basename(
            source_path
        )

        page = resolve_page(
            doc.metadata.get("parent_id")
        )

        page_label = page if page is not None else "Unknown"

        key = f"{source_name}_{page_label}"

        if key not in shown:
            shown.add(key)

            with st.expander(
                f"#{idx} 📄 {source_name} — Page {page_label}"
            ):
                st.write("SOURCE:", source_name)
                st.write(doc.page_content)

                encoded_name = source_name.replace(
                    " ",
                    "%20"
                )

                pdf_url = (
                    f"http://localhost:8000/"
                    f"{encoded_name}"
                    f"#page={page_label}"
                )
                

                st.markdown(
                    f"[📖 Open Page {page_label}]({pdf_url})"
                )