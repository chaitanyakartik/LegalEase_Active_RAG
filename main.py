import urllib.request
from src.rag_helpers.extract_context import extract_context
from src.rag_helpers.vectorstore_functions import vectorstore_setup_main
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from base64 import b64decode
from typing import Any, Dict, Iterator, List, Optional
import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from PIL import Image



  # Display the image using matplotlib
  plt.imshow(image)
  plt.axis('off')  # Turn off axis
  plt.show()

dotenv.load_dotenv(dotenv_path=".env")
def main():
    url = "https://sgp.fas.org/crs/misc/IF10244.pdf"
    filename = "wildfire_stats.pdf"
    urllib.request.urlretrieve(url, filename) 
    path = "/data/"

    data = extract_context(filename)
    #data is a dict with text and images

    #this sets up the vector database
    vectorstore_setup_main(data)

    #RAG pipeline
    #model is the gemini multimodal model were using
    prompt_template = PromptTemplate(
        input_variables=["query", "text", "images"],
        template="This is the query {query}, answer with only the context i will be providing whihc will be\
        texts and images. text : {text}, images: {images}?. if there are no images use the text only"
    )


    mdel = GeminiLLM(api_key = gemini_api_key, model_name = 'gemini-1.5-flash')
    chain = LLMChain(llm=mdel, prompt=prompt_template)

    query = "What is the change in wild fires from 2018 to 2022?"

    docs = retriever.get_relevant_documents( query )
    images, text = split_image_text_types(docs)

    response = chain.run(query=query, text = " ".join(text), images= " ".join(images))

    #One Feedback Iteration  
    query = "i want you to evalute the following answer based on how accurate it\
    is with respect to the given context. If it is not, i want you to give me ways to improve it. Use what context you have  "

    feedback_response = model.generate_content(query+response+"Context:  "+" ".join(text))

    query = "I will give you the question, context,answer and how to make it better. make it better, nothing more  "
    question = "What is the change in wild fires from 2018 to 2022?"

    final_response = model.generate_content(query+ 
                                    "question "+ question +
                                    "context: "+ " ".join(text) +
                                    "answer: "+response+
                                    "how to make it better "+feedback_response.text)

def split_image_text_types(docs):
    ''' Split base64-encoded images and texts '''
    b64 = []
    text = []
    for doc in docs:
        try:
            b64decode(doc)
            b64.append(doc)
        except Exception as e:
            text.append(doc)
    return b64, text

class GeminiLLM(LLM):
    """A custom wrapper for the Gemini model."""
    api_key: str
    model_name: str

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the LLM on the given input."""

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)

        response = model.generate_content(prompt)
        return response.text  # Adjust based on actual response structure

    @property
    def _llm_type(self) -> str:
        return "gemini"

def display_b64images(images: list):
    for img in images:
    image_data = base64.b64decode(img)
    # Open the image
    image = Image.open(BytesIO(image_data))

if __name__ == "__main__":
    main()
    