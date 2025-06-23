import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
# --- IMPORTANT: AUTHENTICATION ---
# For local development, gcloud CLI handles authentication using Application Default Credentials.
# Ensure you've run 'gcloud auth application-default login' (or gcloud init and followed prompts).
# No need for a service account key file for local testing with properly configured gcloud.

# Initialize Firebase Admin SDK (this uses your gcloud default credentials)
# Check if the app is already initialized to prevent re-initialization errors
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

print("Attempting to add a new transaction...")
# 1. Add a new document (transaction)
try:
    doc_ref = db.collection('transactions').document() # Auto-generates a document ID
    new_transaction_data = {
        'amount': 25.75,
        'description': 'Coffee and a snack',
        'category': 'Food',
        'date': '2025-06-20' # Using current date for example
    }
    doc_ref.set(new_transaction_data)
    print(f"Successfully added document with ID: {doc_ref.id}")
except Exception as e:
    print(f"Error adding document: {e}")
    # If you see "Permission denied", double-check your Firestore rules are 'if true;'

print("\n--- All Transactions from Firestore ---")
# 2. Read documents (transactions)
try:
    transactions_ref = db.collection('transactions')
    docs = transactions_ref.stream() # Get all documents in the collection

    found_documents = False
    for doc in docs:
        found_documents = True
        print(f"{doc.id} => {doc.to_dict()}")
    if not found_documents:
        print("No documents found in 'transactions' collection.")
except Exception as e:
    print(f"Error reading documents: {e}")

print("\nFirestore connection test complete!")
