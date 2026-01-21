# Resonance Engine
 **Industrial-grade, telemetry-driven orchestration for immersive RPG soundscapes.**

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Poetry](https://img.shields.io/badge/Packaging-Poetry-60A5FA.svg)](https://python-poetry.org/)

**Resonance Engine** is a reactive middleware designed to bridge the gap between tabletop RPG telemetry (hit points, stress levels, narrative triggers) and dynamic auditory environments. Leveraging the Spotify Web API, the engine orchestrates soundscapes in real-time, ensuring the musical atmosphere is always in resonance with the heartbeat of the story.

---

## 🏗️ Architecture & Design Patterns

The project is built on **Clean Architecture** principles to ensure low coupling and high maintainability:

* **Provider Pattern**: Music services (Spotify) and storage backends (Firebase/DiskCache) are abstracted through rigid interfaces. This allows for hot-swapping providers without modifying core business logic.
* **Stateless Orchestration**: A central "Brain" processes incoming telemetry, evaluates rule-based strategies, and delegates execution to background workers.
* **Factory Pattern**: Centralized service instantiation ensures consistent configuration and efficient resource management.
* **Dependency Injection**: FastAPI’s DI system is used to inject services into routes, facilitating mock-based testing and decoupling.



---

## ⚡ Technical Highlights

* **Non-Blocking I/O**: High-latency external API calls (Spotify) are handled via `BackgroundTasks`, keeping the API response time consistently under 50ms.
* **Deterministic Caching**: Integrated `DiskCache` (SQLite-backed) provides sub-millisecond access to session states while maintaining persistence across restarts.
* **Strict Data Validation**: Powered by `Pydantic`, the engine enforces data integrity with custom validators that neutralize "Falsy traps" and prevent corrupted metrics (NaN/Inf).
* **Spotify Recommendation Engine**: Instead of static playlist switching, it calculates target `Energy`, `Valence`, and `Danceability` to find the perfect track for the current game state.

---

## 🧪 Stress Testing & QA

Resonance Engine is built to be "unbreakable" through a rigorous testing suite:

* **Property-Based Testing**: Powered by `Hypothesis` to generate thousands of edge-case scenarios (extreme values, invalid types) to verify schema robustness.
* **Concurrency Analysis**: Simulated parallel telemetry streams verify thread-safety and database locking mechanisms during high-load gameplay.



---

## 🚀 Getting Started

### Prerequisites
* Python 3.9+
* Poetry (Recommended) or venv

### Installation
```bash
# Clone the repository
git clone [https://github.com/your-username/resonance-engine.git](https://github.com/your-username/resonance-engine.git)
cd resonance-engine

# Install dependencies via Poetry
poetry install

# Configure environment variables
cp .env.example .env
# Edit .env with your Spotify Client ID and Secret

### Running the Engine 

# Activate the virtual environment
poetry shell

# Start the development server
uvicorn main:app --reload

### Running tests

# Execute the stress test suite
pytest tests/


---

## ⚙️ Configuration (.env)

Variable,Description
SPOTIFY_CLIENT_ID,Your Spotify Application ID
SPOTIFY_CLIENT_SECRET,Your Spotify Application Secret
DB_TYPE,Type of DB to use (disk or firebase)
CACHE_TYPE,Caching layer (disk or memory)


---


## ⚖️ License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**. 

### 🚫 Non-Commercial Use
You are free to share and adapt the material for non-commercial purposes, provided that you give appropriate credit and distribute your contributions under the same license.

### 💰 Commercial Use
**Commercial use is strictly prohibited under the current license.** If you wish to use Resonance Engine for commercial purposes, including but not limited to:
* Integrating the engine into a paid application or service.
* Using the engine for monetized streaming events or public performances.
* Redistribution as part of a commercial product.

Please contact the author to discuss a **commercial license agreement**.

---

## 📩 Contact

**Project Lead** - [Giovanni Siragusa]
* **Email**: [gioandro91@gmail.com]

---

*Crafted for Game Masters who demand technical excellence.*