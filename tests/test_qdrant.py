from qdrant_client import QdrantClient
try:
    client = QdrantClient(
        url="https://e4837ced-7c28-4e3a-a206-245ed54f7f20.sa-east-1-0.aws.cloud.qdrant.io",
        api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjcyNzUzOGItMjJkZi00YzhkLWIwOTQtMmRiNTg1NTVkM2Y4In0.EElU7AdqIqU1PNvFoYcjvvPKG2zv9ub5fgAKTF_jlDs"
    )
    colls = client.get_collections()
    print("Success! Collections:", colls)
    
    # Try the other URL with this key just in case
    client2 = QdrantClient(
        url="https://b71bcdc9-7c57-4e57-a5fb-ada7fab81909.eu-west-1-0.aws.cloud.qdrant.io",
        api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjcyNzUzOGItMjJkZi00YzhkLWIwOTQtMmRiNTg1NTVkM2Y4In0.EElU7AdqIqU1PNvFoYcjvvPKG2zv9ub5fgAKTF_jlDs"
    )
    colls2 = client2.get_collections()
    print("Success 2! Collections:", colls2)
except Exception as e:
    print("Error:", e)
