import streamlit as st

from src.rag import answer_question


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="SBI Mutual Fund Facts Assistant",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# Custom styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        /* Main page */
        .stApp {
            background:
                radial-gradient(circle at 15% 10%, rgba(90, 120, 255, 0.10), transparent 28%),
                radial-gradient(circle at 85% 5%, rgba(0, 190, 170, 0.08), transparent 25%),
                #0b0d12;
        }

        .block-container {
            max-width: 1050px;
            padding-top: 3.5rem;
            padding-bottom: 3rem;
        }

        /* Hero */
        .hero {
            padding: 2.2rem 2.3rem;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 24px;
            background: linear-gradient(
                135deg,
                rgba(30, 35, 50, 0.96),
                rgba(18, 22, 31, 0.96)
            );
            box-shadow: 0 20px 60px rgba(0,0,0,0.28);
            margin-bottom: 1.4rem;
        }

        .eyebrow {
            color: #8ea2ff;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.7rem;
        }

        .hero-title {
            font-size: 2.7rem;
            line-height: 1.08;
            font-weight: 800;
            margin: 0;
            color: #f5f7fb;
        }

        .hero-subtitle {
            color: #b8becb;
            font-size: 1.02rem;
            line-height: 1.65;
            margin-top: 0.9rem;
            max-width: 760px;
        }

        .badge {
            display: inline-block;
            margin-top: 1.1rem;
            padding: 0.42rem 0.75rem;
            border-radius: 999px;
            background: rgba(48, 196, 160, 0.10);
            border: 1px solid rgba(48, 196, 160, 0.28);
            color: #6fe0c1;
            font-size: 0.82rem;
            font-weight: 650;
        }

        /* Info cards */
        .info-card {
            min-height: 105px;
            padding: 1rem 1.1rem;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            background: rgba(255,255,255,0.035);
        }

        .info-number {
            font-size: 1.55rem;
            font-weight: 800;
            color: #f4f6fb;
        }

        .info-label {
            margin-top: 0.2rem;
            color: #969dab;
            font-size: 0.82rem;
        }

        /* Section headings */
        .section-title {
            font-size: 1.25rem;
            font-weight: 750;
            color: #f1f3f7;
            margin: 1.7rem 0 0.75rem 0;
        }

        .section-caption {
            color: #8f96a4;
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
        }

        /* Answer */
        .answer-card {
            padding: 1.35rem 1.45rem;
            border-radius: 18px;
            border: 1px solid rgba(142,162,255,0.22);
            background: rgba(142,162,255,0.055);
            margin-top: 0.5rem;
        }

        .answer-label {
            color: #9eafff;
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.10em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        /* Disclaimer */
        .disclaimer {
            margin-top: 2rem;
            padding: 1rem 1.15rem;
            border-radius: 14px;
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.07);
            color: #969dab;
            font-size: 0.82rem;
            line-height: 1.55;
        }

        /* Streamlit buttons */
        div.stButton > button {
            border-radius: 12px;
            min-height: 2.8rem;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.035);
            transition: all 0.15s ease;
        }

        div.stButton > button:hover {
            border-color: rgba(142,162,255,0.55);
            background: rgba(142,162,255,0.08);
        }

        /* Input */
        div[data-baseweb="input"] {
            border-radius: 12px;
        }

        /* Hide Streamlit footer */
        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Hero
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Facts-only mutual fund assistant</div>
        <div class="hero-title">SBI Mutual Fund<br>Facts Assistant</div>
        <div class="hero-subtitle">
            Get concise, citation-backed answers about selected SBI Mutual Fund
            schemes using information collected from official public sources.
        </div>
        <div class="badge">✓ No investment advice · Official sources only</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Quick facts
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-number">15</div>
            <div class="info-label">Official public sources</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-number">4</div>
            <div class="info-label">SBI schemes covered</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-number">Facts</div>
            <div class="info-label">No recommendations or portfolio advice</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Example questions
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Try asking</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-caption">Start with one of these factual questions.</div>',
    unsafe_allow_html=True,
)

example_questions = [
    "What is the minimum SIP amount for SBI ELSS Tax Saver Fund?",
    "What is the benchmark of SBI Multicap Fund?",
    "How do I download my account statement?",
]

for question in example_questions:
    if st.button(
        question,
        use_container_width=True,
        key=f"example_{question}",
    ):
        st.session_state["question"] = question
        st.rerun()


# ---------------------------------------------------------
# Question input
# ---------------------------------------------------------

question = st.text_input(
    "Your question",
    value=st.session_state.get("question", ""),
    placeholder="e.g. What is the exit load of SBI Flexicap Fund?",
    label_visibility="visible",
)


if st.button(
    "Ask the assistant",
    type="primary",
    use_container_width=True,
):

    if not question.strip():

        st.warning("Please enter a mutual fund question.")

    else:

        with st.spinner(
            "Checking official sources..."
        ):

            answer = answer_question(question)

        st.markdown(
            '<div class="answer-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="answer-label">Answer</div>',
            unsafe_allow_html=True,
        )

        st.markdown(answer)

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Footer disclaimer
# ---------------------------------------------------------

st.markdown(
    """
    <div class="disclaimer">
        <strong>Facts-only disclaimer:</strong>
        This assistant provides factual information about the selected
        mutual fund schemes using official public sources. It does not
        provide investment advice, recommendations, portfolio guidance,
        performance-based comparisons, or personalized financial advice.
        Do not enter PAN, Aadhaar, OTPs, account numbers, phone numbers,
        email addresses, or other personal information.
    </div>
    """,
    unsafe_allow_html=True,
)
