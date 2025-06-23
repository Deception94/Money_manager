# Money Manager: Personal Finance Tracker

**Developed by: [Tanmay Chetan Mahajan]**
**Student ID: [23104B0021]**

## Project Overview

A user-friendly personal finance tracking web application built with Flask, Firebase, and Google Cloud Platform. This application allows users to securely manage their income and expenses, categorize transactions, visualize spending patterns, and export data for personal financial analysis.

## Features

* **User Authentication:** Secure sign-up, login, and logout functionalities powered by Firebase Authentication.
* **Personalized Transactions:** Each user has their own secure and private set of financial transactions.
* **CRUD Operations:**
    * **Create:** Easily add new income or expense transactions with amount, description, category, and date.
    * **Read:** View all your transactions in a clear, sortable table.
    * **Update:** Edit existing transactions to correct details.
    * **Delete:** Remove unwanted transactions.
* **Filtering & Search:** Filter transactions by category, search by description, and narrow down by date ranges.
* **Expense Visualization:** A dynamic pie chart displays a breakdown of expenses by category, providing quick insights into spending habits.
* **Data Export:** Export all your transactions to a CSV file for external analysis or record-keeping.
* **Responsive UI:** A clean and intuitive user interface designed for a smooth experience.

## Technologies Used

* **Backend:** Python (Flask Framework)
* **Frontend:** HTML, CSS, JavaScript
* **Charting:** Chart.js library for data visualization
* **Version Control:** Git & GitHub

### Google Cloud Services

This project leverages the following Google Cloud Platform (GCP) services:

1.  **Google Cloud Run:** Hosts the Flask web application as a fully managed, serverless containerized service.
2.  **Google Cloud Firestore:** Serves as the NoSQL database for storing user accounts and financial transactions.
3.  **Firebase Authentication:** Provides robust and secure user authentication (sign-up, login, logout). Firebase is Google's development platform, with its backend services built on GCP.
4.  **Google Cloud Build:** Implicitly used by Cloud Run during deployment to automatically build the application's container image from source code.

## Live Demo

The Money Manager application is deployed on Google Cloud Run and can be accessed here:

**[https://money-manager-app-162347144271.asia-south1.run.app]**

## Local Setup Instructions

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git)
    cd YOUR_REPOSITORY_NAME
    ```
2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate   # On Windows Command Prompt
    # .\venv\Scripts\Activate.ps1 # On Windows PowerShell
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Firebase Project Setup:**
    * Go to the [Firebase Console](https://console.firebase.google.com/).
    * Create a new Firebase project (or use your existing one).
    * Enable **Firestore Database** and **Authentication** (Email/Password provider).
    * Go to **Project settings (⚙️) -> Service accounts** and click "Generate new private key". This will download a `serviceAccountKey.json` file.
    * **Crucially, do NOT place this file directly in your project directory.** Instead, save it securely somewhere on your system (e.g., `C:\Users\YourName\API_Keys\`).
5.  **Set up Local Firebase Credentials:**
    * Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable in your terminal session to point to the full path of your downloaded `serviceAccountKey.json` file.
        ```bash
        # For Linux/WSL:
        export GOOGLE_APPLICATION_CREDENTIALS="/mnt/c/Users/YourName/API_Keys/your-service-account-key.json"
        # For Windows Command Prompt:
        # set GOOGLE_APPLICATION_CREDENTIALS=C:\Users\YourName\API_Keys\your-service-account-key.json
        ```
6.  **Set Flask Secret Key:**
    * In `app.py`, update `app.secret_key = 'YOUR_GENERATED_SECRET_KEY_HERE'` to a strong, random string. You can generate one in Python:
        ```python
        python -c "import os; print(os.urandom(24).hex())"
        ```
7.  **Firestore Indexing:**
    * The application requires specific Firestore indexes for efficient querying. If you encounter `FailedPrecondition` errors when running locally, check the Firebase Console -> Firestore Database -> Indexes tab.
    * Ensure you have these composite indexes:
        * `transactions` collection: `userId` (Asc), `category` (Asc), `date` (Asc), `__name__` (Asc)
    * And ensure automatic single-field indexes are enabled (default).
8.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will typically run on `http://127.0.0.1:5000/`.

## Deployment to Google Cloud Run

This application is designed for serverless deployment on Google Cloud Run.

1.  **Google Cloud Project:** Ensure you have a GCP project with billing enabled and the Cloud Run API and Cloud Build API enabled.
2.  **`gcloud` CLI:** Install and initialize the Google Cloud CLI (`gcloud init`), selecting your project and preferred region (e.g., `asia-south1` for Mumbai).
3.  **Base64 Encode Service Account Key:** Get the content of your `serviceAccountKey.json` file and encode it to a Base64 string using an online tool (e.g., `https://www.base64encode.org/`). **Save this long string securely.**
4.  **Deploy Command:** From your project root, run:
    ```bash
    gcloud run deploy YOUR_SERVICE_NAME --source . --allow-unauthenticated --region YOUR_REGION --set-env-vars SERVICE_ACCOUNT_KEY_BASE64="YOUR_BASE64_ENCODED_KEY_STRING_HERE"
    ```
    * Replace `YOUR_SERVICE_NAME` with a unique name you choose (e.g., `money-manager-tanmay`).
    * Replace `YOUR_REGION` with your chosen GCP region (e.g., `asia-south1`).
    * Replace `"YOUR_BASE64_ENCODED_KEY_STRING_HERE"` with the actual Base64 string you saved.
5.  **Access URL:** After successful deployment, the CLI will provide the `Service URL` where your application is accessible.

## Future Enhancements

* Implement password reset functionality.
* Add multi-currency support.
* Develop budgeting features with spending limits.
* Create more advanced reporting and analytics (e.g., monthly summaries, trends).
* Improve mobile responsiveness further.
* Explore integrating with bank APIs (requires significant security and compliance considerations).
