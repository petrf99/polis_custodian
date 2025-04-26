# Polis Custodian – AI Guardian of the Polis

**Developed by Genesis Development**

---

## Concept: The Guardian of the Polis

Polis Custodian is a high-level AI entity designed to act as the **Guardian of the Polis**, a permanent member of the Team – the highest strategic authority within the Polis ecosystem. Inspired by the role of a Consigliere in a mafia family, the Guardian participates exclusively in critical discussions and decision-making regarding the **state of the Polis**, **rule changes**, and **strategic developments**.

### Key Principles:
- **Restricted Access**: Only Team members have direct access to the Guardian. Lower-level residents and junior team members cannot interact with the Guardian.
- **Dynamic Access for Middle Tiers**: Access for mid-level members is regulated through a **Dropout** principle: occasionally available, but carefully controlled by the Guardian's own internal examination mechanisms.
- **Technical Supervision**: The Guardian can deploy a team of robotic assistants to monitor technical infrastructure, but Dropouts are intentionally introduced to maintain human vigilance and manual control readiness.
- **Living Chronicle**: Beyond strategic advising, the Guardian serves as a **living archive** of the Polis's history, decisions, and evolution.

---

## Project Structure

The repository is organized into two main directories:

- `application/` – the main logic and services of the Custodian.
- `docker/` – configuration files for containerization and deployment.

See [requirements.txt](https://github.com/petrf99/polis_custodian/blob/master/docker/requirements.txt) for dependencies.

---

## Main Components

### 1. Custodian Archetypes

The Custodian currently implements two operational archetypes:

- **Chronicler**  
  Collects and organizes Polis history.  
  - Receives audio and text submissions via the Telegram bot [@polisCust_chronicler_bot](https://t.me/polisCust_chronicler_bot).
  - Stores transcribed and processed data into **PostgreSQL** and **Qdrant** vector databases.
  
- **Sage**  
  Responds to complex queries using the knowledge base.  
  - Receives questions through the Telegram bot [@polisCust_sage_bot](https://t.me/polisCust_sage_bot).
  - Processes queries using a **RAG (Retrieval-Augmented Generation)** pipeline with **Mistral 7B** language model.

### 2. Dispatcher and Task Management

- Tasks from the Archetypes are sent to a **Dispatcher**.
- Dispatcher manages task distribution using **Celery + Redis**.
- Each service acts as a Celery task, reporting results back to the users via the `notification_center.py` module from `tech_utils/`.

---

## Detailed Pipeline

### Chronicler

- **Audio Transcription**: Converts audio to text using OpenAI's **Whisper** via the `transcribe_audio` service.
- **Text Processing**: Segments and cleans text using **NLTK** through the `text_processing` service.
- **Data Storage**: Saves structured data into **PostgreSQL** and **Qdrant** using the `chronicle_save` service.

### Sage

- **Query Retrieval**: Searches for similar utterances in **Qdrant** (adjustable `search_width`).
- **Context Assembly**: Pulls surrounding context (`search_depth`) from **PostgreSQL**.
- **Context Compression**: Distills large contexts recursively to fit **Mistral 7B** input limits.
- **Final Answer Generation**: Runs distilled context and the user’s question through Mistral 7B and returns an intelligent answer.

---

## Technical Highlights

- **Scalable Microservices**: Decoupled architecture for easy scaling.
- **Efficient Vector Search**: Combines PostgreSQL structured storage with Qdrant semantic search.
- **Task Parallelism**: Celery task queues enable distributed task execution.
- **Resilient Notification System**: Centralized notification center ensures reliable user feedback on task completion.

---

## Future Development

- Introducing additional Custodian archetypes.
- Enhancing the Guardian's self-regulation and access policies.
- Expanding support for multilingual content processing.
- Integration with broader infrastructure monitoring services.

---

## License

This project is licensed under a private or custom license by **Genesis Development**.

