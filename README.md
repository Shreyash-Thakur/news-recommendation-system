
# News Recommendation System

## Overview
The News Recommendation System is a robust, scalable platform designed to deliver personalized news article suggestions using advanced machine learning and natural language processing techniques. It leverages embeddings for content-based recommendations and supports efficient data ingestion, cleaning, and storage workflows.

## Features
- Automated news article scraping and ingestion
- Text cleaning and preprocessing pipeline
- Embedding generation for articles
- Duplicate detection and removal
- PostgreSQL database integration via Docker
- Modular Python codebase for easy extension

## Technology Stack
- Python 3.x
- PostgreSQL (Dockerized)
- Docker & Docker Compose
- Machine Learning: Embeddings-based recommender

## Setup Instructions
1. **Install Docker Desktop**  
  Download and install from [docker.com](https://www.docker.com/products/docker-desktop/). Restart your system and launch Docker Desktop.

2. **Start PostgreSQL Database**  
  Run the following command to start the database:
  ```powershell
  docker-compose up -d
  ```

3. **Install Python Dependencies**  
  ```powershell
  pip install -r requirements.txt
  ```

4. **Initialize the Database**  
  ```powershell
  python setup_database.py
  ```

5. **Ingest News Articles**  
  ```powershell
  python refresh_articles.py
  ```

For advanced Docker setup, see [docker-setup.md](docker-setup.md).

## Project Structure
- `setup_database.py` — Database schema creation
- `scraper.py` — News article scraping logic
- `text_cleaner.py` — Text cleaning utilities
- `refresh_articles.py` — Main ingestion pipeline
- `config.py` — Configuration management
- `recommender_embeddings.py` — Embedding-based recommendation engine
- `remove_duplicates.py` — Duplicate detection and removal
- `requirements.txt` — Python dependencies
- `Dockerfile` & `docker-compose.yml` — Containerization

## Database Schema
The core table is `articles`:

| Column         | Type         | Description           |
| -------------- | ------------ | --------------------- |
| id             | SERIAL       | Primary key           |
| title          | TEXT         | Article title         |
| content        | TEXT         | Full article content  |
| category       | TEXT         | News category         |
| published_date | TIMESTAMP    | Publication date      |
| source         | TEXT         | Source name           |
| url            | TEXT         | Article URL           |
| created_at     | TIMESTAMP    | Ingestion timestamp   |

## Usage
After setup, you can run the main pipeline scripts to ingest, clean, and recommend articles. Extend the recommender logic in `recommender_embeddings.py` for custom ML models.

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request. For major changes, open an issue first to discuss your proposal.

## License
Distributed under the MIT License. See `LICENSE` for details.
