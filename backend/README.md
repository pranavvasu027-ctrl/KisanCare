# KisanCare Backend

This is the backend service for KisanCare, built with FastAPI.

## Current Status
Currently in **Phase 0**. The backend provides a basic `/health` endpoint.

**Note:** The Crop Recommendation API is NOT implemented yet. We will connect the trained model after Model 1 has been properly trained and evaluated in Google Colab.

## Running the Backend locally
To run the backend, ensure you have installed the requirements, then execute:

```bash
uvicorn backend.app.main:app --reload
```
