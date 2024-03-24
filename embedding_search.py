import os
import nltk
import sqlite3
import time
import numpy as np
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util
import torch

# Initialize NLTK tokenizer if not already downloaded
if not os.path.exists(nltk.data.find('tokenizers/punkt')):
    nltk.download('punkt')

# Initialize SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_or_connect_to_database(filename):
    # Create a database connection
    conn = sqlite3.connect(f'databases/{filename}_embeddings.db')
    c = conn.cursor()
    
    # Create table to store text embeddings if not exists
    c.execute("CREATE TABLE IF NOT EXISTS embeddings (text TEXT PRIMARY KEY, embedding TEXT)")
    
    # Create metadata table if not exists
    c.execute("CREATE TABLE IF NOT EXISTS metadata (last_modified_time REAL)")
    
    # Check if metadata exists, if not insert current time
    c.execute("SELECT * FROM metadata")
    row = c.fetchone()
    if not row:
        last_modified_time = os.path.getmtime(filename)
        c.execute("INSERT INTO metadata VALUES (?)", (last_modified_time,))
        conn.commit()
    
    return conn, c

def close_database_connection(conn):
    # Close database connection
    conn.close()

def compute_similarity(conn, c, texts, query, filename):
    # Check if embeddings need to be recomputed based on file modification time
    last_modified_time = os.path.getmtime(filename)
    c.execute("SELECT last_modified_time FROM metadata")
    row = c.fetchone()
    if row and row[0] == last_modified_time:
        # Use existing embeddings
        embeddings = []
        for text in texts:
            c.execute("SELECT embedding FROM embeddings WHERE text=?", (text,))
            row = c.fetchone()
            if row:
                embedding = np.fromstring(row[0], dtype=np.float32, sep=',')
                embeddings.append(embedding)
            else:
                # If embedding is missing, recompute it
                embedding = model.encode([text])[0]
                c.execute("INSERT INTO embeddings VALUES (?, ?)", (text, ','.join(map(str, embedding))))
                conn.commit()
                embeddings.append(embedding)
    else:
        # Recompute all embeddings if file is modified
        embeddings = [model.encode([text])[0] for text in texts]
        # Update metadata
        c.execute("UPDATE metadata SET last_modified_time=?", (last_modified_time,))
        conn.commit()
        # Update embeddings
        c.execute("DELETE FROM embeddings")
        for text, embedding in zip(texts, embeddings):
            c.execute("INSERT INTO embeddings VALUES (?, ?)", (text, ','.join(map(str, embedding))))
        conn.commit()
    
    # Convert embeddings to a single numpy array
    embeddings_array = np.stack(embeddings)
    
    # Convert numpy array to tensor
    embeddings_tensor = torch.tensor(embeddings_array)
    
    # Compute similarity with the query
    query_embedding = model.encode([query])
    query_tensor = torch.tensor(query_embedding)
    similarities = util.pytorch_cos_sim(embeddings_tensor, query_tensor)
    
    text_sim_pair = list(zip(similarities.tolist(), texts))
    sorted_similarities = sorted(text_sim_pair, reverse=True)
    
    return sorted_similarities

def tokenize_sentences(text, max_sentence_length):
    sentences = sent_tokenize(text)
    short_sentences = [s for s in sentences if len(s.split()) <= max_sentence_length]
    return short_sentences

def read_file(filename):
    with open(f"uploads/{filename}", "r") as f:
        content = "".join(f.readlines())
    return content

def write_html(filename, texts):
    with open(f"html_storages/{filename}.html", "w") as f:
        write_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Highlighted Text</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 40px;
                }}
                .highlight {{
                    background-color: #ffff66; /* Yellow background for highlighted text */
                }}
            </style>
        </head>
        <body>
            <p>
                {'.'.join(texts)}
            </p>
        </body>
        </html>
        """
        f.write(write_content)


def highlight_relevant_sentences(texts, similarities, confidence):
    highlighted_texts = texts.copy()
    for sim in similarities:
        if sim[0][0] > confidence:
            highlighted_texts[highlighted_texts.index(sim[1])] = f"<b class='highlight'> {sim[1].strip()} </b> ({sim[0][0]:.2f})"
    return highlighted_texts

def run_highlight(filename, query, confidence):
    # Create or connect to database
    conn, c = create_or_connect_to_database(filename)

    # Read content from file and tokenize sentences
    content = read_file(filename)
    texts = tokenize_sentences(content, 100)

    # Compute similarities between sentences and query
    similarities = compute_similarity(conn, c, texts, query, filename)

    # Highlight relevant sentences based on confidence level
    highlighted_texts = highlight_relevant_sentences(texts, similarities, confidence)

    # Write highlighted texts to HTML file
    write_html(filename, highlighted_texts)

    # Close database connection
    close_database_connection(conn)

def run_get_relevant(filename, query, n):
    # Create or connect to database
    conn, c = create_or_connect_to_database(filename)

    # Read content from file and tokenize sentences
    content = read_file(filename)
    texts = tokenize_sentences(content, 100)

    # Compute similarities between sentences and query
    similarities = compute_similarity(conn, c, texts, query, filename)

    # Print the first n sentences with the highest similarity score
    top_sentences = []
    for sim in similarities[:n]:
        top_sentences.append(f"{sim[1]} ({sim[0][0]:.2f})")

    # Close database connection
    close_database_connection(conn)
    return top_sentences



# if __name__ == "__main__":
#     filename = "script.txt"
#     query = "carbon cycle"
#     confidence = 0.5
#     n = 5
#     run_highlight(filename, query, confidence) 
#     run_get_relevant(filename, query, n)
















