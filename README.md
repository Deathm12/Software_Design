# Software & Design

This repository contains several mini-projects developed for the Software & Design course at Epitech China.

## Table of Contents
- [1. Battleship (pygame, network)](#1-battleship)
- [2. Physics (Physics demos with pygame)](#2-physics)

---

## 1. Battleship

A networked battleship game with a graphical interface (pygame).

- **Folder:** `game/bataille_naval/`
- **Files:**
  - `client.py`: Launches the graphical client (pygame)
  - `server.py`: Launches the game server (2 players)

### How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python game/bataille_naval/server.py
   ```
3. Start a client (in another terminal, twice for two players):
   ```bash
   python game/bataille_naval/client.py
   ```

---

## 2. Physics

Two small interactive physics demos with pygame:
- `physic.py`: Interactive ball with gravity and bounce
- `gjk_physic.py`: Collision detection demo (GJK algorithm)

- **Folder:** `Physics/`

### How to Run
Install pygame if needed:
```bash
pip install -r requirements.txt
```

Run a demo:
```bash
python Physics/physic.py
# or
python Physics/gjk_physic.py
```

---

## Dependencies
- Python 3.x
- pygame (for graphical projects)

To install all dependencies for all projects, simply run:
```bash
pip install -r requirements.txt
```