import google.generativeai as genai
import base64
import uuid
from langchain.vectorstores import Chroma
from langchain.storage import InMemoryStore
from langchain.schema.document import Document
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.embeddings import SentenceTransformerEmbeddings

def vectorstore_setup_main(input_dict: dict) :
    my_api_key = os.getenv("GEMINI_API_KEY")

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = "Describe the image in detail. Be specific about graphs, such as bar plots."
    visual_descriptions = []
    for img in image_list:
        with open(img, "rb") as image_file:
                image_data = image_file.read()  # Read image data as binary

        image_data_base64 = base64.b64encode(image_data).decode('utf-8')
        response = model.generate_content([prompt, image_data_base64])
        visual_descriptions.append(response.text)

    # Text oart
    long_string = input_dict['text']
    text_chunks = split_string_into_chunks(long_string)
    #create text summaries using text chunks
    text_summaries = []
    query = " --> Summarize the text in a concise manner"
    for text in text_chunks:
    result = model.generate_content(text+ query)
    text_summaries.append(result.text)

    #-----------------------------
    #text_summaries and visual_descriptions are the descriptions lists

    setup_vector_db({"text_summaries": text_summaries, "visual_description_summaries": visual_description_summaries})

def split_string_into_chunks(long_text, max_chunk_size=3000):
    # Create a list to hold the chunks
    chunks = []

    # Iterate over the text, slicing it into chunks
    for start_index in range(0, len(long_text), max_chunk_size):
        end_index = start_index + max_chunk_size
        chunk = long_text[start_index:end_index]  # Extract the chunk
        chunks.append(chunk)  # Add the chunk to the list

    return chunks

def setup_vector_db(input_dict: dict):
    embedding_model = SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2')

    # The vectorstore to use to index the child chunks
    vectorstore = Chroma(collection_name="multi_modal_rag",
                        embedding_function=embedding_model)

    # The storage layer for the parent documents
    store = InMemoryStore()
    id_key = "doc_id"

    # The retriever (empty to start)
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=store,
        id_key=id_key,
    )

    text_summaries_id = [str(uuid.uuid4()) for _ in text_summaries]
    visual_descriptions_id = [str(uuid.uuid4()) for _ in visual_descriptions]


    text_summaries_docs = []
    # Loop through each text summary and its corresponding document ID
    for i in range(len(text_summaries)):
        summary = text_summaries[i]  # Get the current summary
        doc_id = text_summaries_id[i]  # Get the corresponding document ID

        # Create a Document object with the summary and document ID as metadata
        doc = Document(page_content=summary, metadata={id_key: doc_id})

        # Add the Document to the summary_texts list
        text_summaries_docs.append(doc)

    visual_descriptions_docs = []
    # Loop through each text summary and its corresponding document ID
    for i in range(len(text_summaries)):
        summary = text_summaries[i]  # Get the current summary
        doc_id = text_summaries_id[i]  # Get the corresponding document ID

        # Create a Document object with the summary and document ID as metadata
        doc = Document(page_content=summary, metadata={id_key: doc_id})

        # Add the Document to the summary_texts list
        visual_descriptions_docs.append(doc)

    retriever.vectorstore.add_documents(text_summaries_docs)
    retriever.docstore.mset(list(zip(text_summaries_id, text_chunks)))

    retriever.vectorstore.add_documents(visual_descriptions_docs)
    retriever.docstore.mset(list(zip(visual_descriptions_id, base64_images)))