Problem Statement:
Understanding legal processes in India can feel overwhelming, especially for people who don’t speak English or lack access to affordable legal help. Many struggle with:

-Language Barriers
-Making sense of complex legal documents or precedents.
-Creating forms or documents for their personal legal needs.
Proposed Solution:
A user-friendly law-based chatbot that helps people navigate legal challenges, with features like:

Indian Language Voice Support:
User based context answer generation: Takes user input as documents for user context
Pre-stored Legal Resources: Access the Constitution, key precedents, and summaries of important judgments instantly.
Legal Document Generator: Quickly create forms, contracts, or other documents based on a few simple inputs.
User Document Insights: Upload your legal documents to get helpful insights, summaries, or checks for compliance.

Impact:
This chatbot makes legal help simple, accessible, and affordable for everyone, especially those in rural areas or non-English-speaking communities. It empowers users to confidently handle basic legal tasks and understand their rights better.

Why RAG?
Legal cases often involve extensive amounts of documentation that need to be analysed to extract key information relevant to the case. RAG helps streamline this process by enabling efficient retrieval and generation of insights from large volumes of legal documents.
Example Use Case: Wrongful Termination Case
Scenario: A person is fighting a company for unlawful termination, citing personal grudge.
Documents Involved:
Deposition Documents: These could range from 20-50 pages per deposition, containing testimony and witness statements.
Employee Handbook/Company Policies: Company rules, including termination policies. Typically medium-sized (~10-30 pages).
Requests for Production: Specific documents requested from the other party, such as emails or records. This could involve a large volume of emails.
Precedent Case Transcripts: Court transcripts from prior proceedings, typically large (~50-100 pages). These provide insights into how similar cases were argued and what evidence was presented.
Legal Treatises or Books: Books on employment law, offering a detailed discussion of legal principles and wrongful termination cases. These can be large (~100-300 pages).

                                        
  
  
![WORK](https://github.com/user-attachments/assets/b36480f1-84db-4167-b625-49f39803c6d6)

Possibly add agentic workflow for document generation, or directly ask LLM to generate the document and return it
Extra Query preprocessing required for voice to text, and output text to voice




Inspiration (Adaptive RAG): https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/
Tool used for flowchart: https://excalidraw.com/


 
