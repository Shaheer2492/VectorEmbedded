# VectorEmbedded
General Overview:
This python script is connecting to a Google Sheets document using the Google Sheets API, and retrieving records from a specific sheet.

It filters these records based on a specific status field, converts them into a dictionary, and then sends this data to OpenAI to create text embeddings using the specified model.

It initializes a Pinecone index and upserts (inserts or updates) the embeddings and associated metadata into this index.

It then generates queries from the records, creates embeddings for these queries, and uses these query embeddings to find the most similar embeddings in the Pinecone index.

The results, including the names and email addresses, are then written to a specific sheet in your Google Sheets document.
