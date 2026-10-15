# ♟️ Say2Check

### Voice-Controlled & Computer-Vision Chess Overlay for Accessible Online Play

**Say2Check** is a multimodal accessibility tool designed primarily to help **chess players with motor impairments** interact with online chess platforms without relying on precise mouse or keyboard input.

The system combines **voice recognition, computer vision, text-to-speech feedback, screen interaction, and a transparent desktop overlay** to provide an alternative way of interacting with online chessboards.

Users can speak chess commands such as `"e2 to e4"`, which Say2Check interprets and translates into interactions with the on-screen chessboard. Users can also request information about piece positions and receive **auditory feedback** generated from computer-vision analysis of the board.

Unlike many voice-controlled chess systems, Say2Check does **not require integration with a chess platform's API or an embedded chess engine**. Instead, it interacts with the chessboard visually through the screen, allowing the core concept to remain independent of the underlying chess platform.

Say2Check was developed as my **Final Year Software Engineering Project**.

---

## ♿ Accessibility First

The primary motivation behind Say2Check is improving online chess accessibility for **players with motor impairments**.

Most online chess interfaces depend heavily on accurate mouse movement, clicking, dragging, or keyboard interaction. These conventional input methods can create significant barriers for players with limited motor control.

Say2Check explores an alternative interaction model where users can:

- 🎙️ Make chess moves using voice commands
- 🖱️ Reduce reliance on precise mouse interaction
- 👁️ Use computer vision to identify pieces on the displayed board
- 🔊 Ask for piece locations and receive spoken feedback
- 🖥️ Interact through an accessibility overlay placed over an existing chess interface
- ♟️ Continue using existing online chess platforms rather than a separate chess application

The objective is **not to play chess on behalf of the user**, but to make interaction with the chessboard more accessible.

---

## 🎓 Teaching Aid & Beginner Support

Although Say2Check was primarily developed as an accessibility tool, the project also has potential as an **interactive teaching aid for chess coaches and beginner players**.

During the project's stakeholder and requirements research, chess coaches were identified as support users, while research participants also indicated that the system could be useful as a beginner-friendly teaching aid.

Say2Check's voice interaction, computer vision and auditory feedback provide opportunities for interactive chess learning.

Potential teaching scenarios include:

- 👨‍🏫 Coaches using the system as an interactive teaching aid
- 🌱 Beginners becoming familiar with chessboard coordinates and piece positions
- 🎙️ Students practising chess square notation through spoken commands
- 🔊 Piece-location feedback reinforcing board awareness
- ♟️ Learners becoming more comfortable with chess notation through voice interaction

> **Note:** Say2Check is not a chess engine and does not provide move recommendations, engine analysis or chess strategy. Its teaching potential comes from interaction, board awareness, coordinate recognition and piece-location feedback.

---

## 🎯 Project Aim

The aim of Say2Check is to develop a **universal screen overlay for online chess platforms** that can identify chess-piece positions, recognize user input through voice commands, and provide voice-based feedback to improve accessibility.

The project particularly focuses on reducing interaction barriers for **players with motor impairments**, while also exploring the system's potential as an interactive tool for chess learning and teaching.

---

## ✨ Key Features

### ♿ Accessibility

- Hands-free chess interaction through voice commands
- Designed primarily for players with motor impairments
- Reduced dependence on precise mouse and keyboard input
- Auditory feedback through text-to-speech
- Voice-based piece-position queries
- Simple desktop overlay interface

### 🎙️ Voice Interaction

- Chess coordinate recognition (`a1` – `h8`)
- Spoken move commands
- Chess-specific command parsing
- Offline speech recognition using Vosk
- Voice-based requests for board information

### 👁️ Computer Vision

- Custom-trained PyTorch chess-piece classifier
- Screen-based chessboard analysis
- Piece identification across chessboard squares
- Piece-location detection
- Visual board information converted into auditory feedback

### 🖥️ Platform Interaction

- Transparent PyQt5 desktop overlay
- Screen-coordinate mapping
- Automated on-screen interaction using PyAutoGUI
- Designed without requiring chess-platform APIs
- No embedded chess engine required
- Modular interaction with existing online chess interfaces

### 🎓 Teaching & Learning

- Potential teaching aid for chess coaches
- Beginner-friendly board interaction
- Spoken coordinate practice
- Piece-location learning through auditory feedback
- Interactive reinforcement of chessboard awareness

---

## 🧠 How Say2Check Works

Say2Check combines several independent components into a multimodal interaction pipeline.

```text
             ┌──────────────────────┐
             │      User Voice      │
             │       Command        │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │  Speech Recognition  │
             │        Vosk          │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │    Chess Command     │
             │       Parser         │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │    Board / Screen    │
             │ Coordinate Mapping   │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │      PyAutoGUI       │
             │  Screen Interaction  │
             └──────────────────────┘


      Screen Capture
             │
             ▼
    ┌──────────────────────┐
    │   Computer Vision    │
    │   PyTorch + OpenCV   │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │   Piece Detection    │
    │   / Classification   │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Text-to-Speech      │
    │      Feedback        │
    └──────────────────────┘
```

At a high level, the system follows two main interaction paths:

**Voice-controlled movement**

```text
Voice Command
     ↓
Speech Recognition
     ↓
Command Parsing
     ↓
Chess Coordinates
     ↓
Screen Coordinates
     ↓
Mouse Interaction
```

**Piece-position feedback**

```text
Voice Query
     ↓
Screen Capture
     ↓
Computer Vision
     ↓
Piece Identification
     ↓
Position Detection
     ↓
Text-to-Speech Feedback
```

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python** | Core application development |
| **PyQt5** | Transparent desktop overlay and GUI |
| **Vosk** | Offline speech recognition |
| **PyTorch** | Chess-piece classification model |
| **Torchvision** | Model architecture and image transformations |
| **OpenCV** | Image processing and board analysis |
| **PyAutoGUI** | Screen capture and mouse interaction |
| **pyttsx3** | Text-to-speech auditory feedback |
| **SoundDevice / PyAudio** | Microphone and audio input |
| **NumPy** | Image and numerical processing |
| **Pillow** | Image preprocessing |

---

## 📂 Project Structure

```text
Say2Check/
│
├── say2check_final.py
├── Say2Check_Integrated_Overlay.py
│
├── chess_listener.py
├── chess_mover.py
│
├── interference_engine.py
│
├── vision_board.py
├── vision_board_v2.py
├── board_watcher_v2.py
│
├── main_overlay.py
├── voice_locator_overlay.py
│
├── chess_ai.pth
├── class_names.txt
├── board_coordinates.json
│
├── train_ai.py
├── test_accuracy.py
├── test_piece_feedback.py
│
├── manual_board.py
├── finder.py
├── move_to_test.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

### Important Components

**`say2check_final.py`**  
Main integrated Say2Check application.

**`chess_listener.py`**  
Handles speech recognition and parsing of chess-related voice commands.

**`chess_mover.py`**  
Converts chessboard coordinates into screen interactions and executes moves.

**`interference_engine.py`**  
Loads and performs inference using the trained chess-piece classification model.

**`vision_board_v2.py`**  
Handles screen-based chessboard analysis.

**`chess_ai.pth`**  
Trained PyTorch model used for chess-piece classification.

**`train_ai.py`**  
Used during development to train the computer-vision model.

**`test_accuracy.py`**  
Used to evaluate the trained piece-classification model.

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/RasinduSen/Say2Check.git
cd Say2Check
```

---

### 2. Create a Virtual Environment

#### Windows PowerShell

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Once activated, your terminal should display something similar to:

```text
(venv) PS C:\...\Say2Check>
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Some of the main dependencies include:

```text
PyQt5
PyTorch
Torchvision
OpenCV
Vosk
PyAutoGUI
pyttsx3
SoundDevice
SpeechRecognition
Pillow
NumPy
```

---

## 🎤 Speech Recognition Model

Say2Check uses **Vosk** for offline speech recognition.

The Vosk language model is not included directly in this repository because model files can be large.

Download a compatible English Vosk model and place it in the location expected by the application.

Example:

```text
Say2Check/
│
├── model/
│   └── [Vosk model files]
│
├── say2check_final.py
└── ...
```

If necessary, update the model path in the application to match the location of your downloaded Vosk model.

---

## ▶️ Running Say2Check

After activating the virtual environment and installing the dependencies, run:

```bash
python say2check_final.py
```

Depending on the version being tested, other development entry points may also exist in the repository.

---

## 🎙️ Example Interaction

A simplified voice-controlled move could look like:

```text
User:
"e2 to e4"

        ↓

Speech Recognition:
"e2 to e4"

        ↓

Command Parser:
Source: e2
Destination: e4

        ↓

Coordinate Mapping:
e2 → screen position
e4 → screen position

        ↓

PyAutoGUI:
Select e2
Select e4
```

For board feedback, a user can request information about a piece and Say2Check can use the computer-vision module to identify its location before returning the result through speech.

---

## 👁️ Computer Vision

Say2Check uses a custom-trained computer-vision model to recognize chess pieces displayed on the screen.

The vision pipeline consists of:

1. Capturing the displayed chessboard
2. Mapping the board into an `8 × 8` grid
3. Processing individual chessboard squares
4. Passing square images through the trained PyTorch model
5. Classifying the contents of the squares
6. Mapping predictions back to chess coordinates
7. Using the detected board state for user feedback

This allows Say2Check to obtain information from the displayed chessboard **without requiring direct access to the chess platform's internal game state**.

---

## 🔊 Piece Position Feedback

One of Say2Check's accessibility-focused features is the ability to provide information about the current board through auditory feedback.

For example, a user may request the position of a particular piece.

The system can then:

```text
Voice Request
      ↓
Speech Recognition
      ↓
Piece Request Identified
      ↓
Computer Vision Analysis
      ↓
Piece Located
      ↓
Chess Coordinate Determined
      ↓
Text-to-Speech Response
```

This feature is particularly relevant to the project's accessibility goals and can also support beginner chess training by reinforcing piece positions and board coordinates.

---

## 🧩 Design Philosophy

Say2Check follows several core design principles:

### Accessibility First

The interaction model should reduce unnecessary dependence on precise physical input and provide alternative methods of interacting with an online chessboard.

### Platform Independence

The system is designed to operate as an external overlay rather than being deeply integrated into one specific chess website.

### Multimodal Interaction

Speech recognition, computer vision, visual interface elements and auditory feedback work together rather than relying on a single interaction method.

### Lightweight Interaction

Say2Check avoids integrating a full chess engine into its core interaction pipeline.

### User Control

The system assists the user in interacting with the board rather than making chess decisions on their behalf.

---

## 🚫 What Say2Check Is Not

Say2Check is **not** designed to be:

- A chess engine
- An automated chess-playing bot
- A move recommendation system
- A Stockfish replacement
- A chess strategy assistant
- An ELO/rating system
- A tool for automatically selecting the best move

The project focuses on **accessibility and human-computer interaction**.

Chess decisions remain with the player.

---

## 🔬 Research Context

Say2Check was developed as a Final Year Project exploring the intersection of:

- Human-Computer Interaction (HCI)
- Accessibility and assistive technology
- Automatic Speech Recognition (ASR)
- Computer Vision
- Machine Learning
- Multimodal interaction
- Desktop overlays
- Accessible gaming

The project investigates how speech recognition and computer vision can be combined to create an alternative interaction layer for existing online chess interfaces.

A major research focus is the use of these technologies to improve access for **users with motor impairments** while maintaining a lightweight and platform-independent architecture.

---

## 🎯 Target Users

### Primary Users

**Chess players with motor impairments**

Players who may experience difficulty using conventional mouse or keyboard interaction can use voice commands and auditory feedback as alternative interaction methods.

### Secondary Users

**Elderly chess players**

Voice interaction may provide an alternative for users who find conventional computer input methods difficult or uncomfortable.

### Support Users

**Chess coaches and beginners**

The voice and board-feedback capabilities can be used to support interactive teaching, chessboard awareness and coordinate learning.

---

## 📊 Evaluation Areas

The Say2Check project considers several areas when evaluating the effectiveness of the system:

- Speech recognition accuracy
- Chess-command recognition
- Chess-piece classification accuracy
- System response time
- Board interaction reliability
- Accessibility
- Ease of use
- User experience
- Cross-platform adaptability
- Effectiveness of auditory feedback

The project also considers usability from the perspective of its intended users, particularly players with motor impairments.

---

## 🔒 Privacy & Offline Processing

A key design consideration of Say2Check is reducing unnecessary dependence on external services.

Vosk allows speech recognition to operate **offline**, while the computer-vision model can also perform inference locally.

This architecture can provide benefits such as:

- Reduced reliance on cloud services
- No requirement to send voice commands to an external speech API
- Reduced network dependency
- Local processing of screen information
- Improved portability

---

## ⚠️ Current Limitations

Say2Check is a research prototype and Final Year Project rather than a production-ready accessibility product.

Current limitations may include:

- Recognition accuracy can vary with microphone quality and background noise
- Different accents may affect speech recognition
- Visually different chessboard themes can affect computer-vision performance
- Screen resolution and board positioning can affect coordinate mapping
- Board calibration may be required
- The current implementation primarily targets English voice commands
- Compatibility may vary between chess interfaces
- The system does not contain full chess logic for move validation
- The project has not been designed to provide engine analysis or strategy recommendations

---

## 🔮 Future Improvements

Possible future development areas include:

- Improved automatic chessboard detection
- More robust support for different chessboard themes
- Improved speech recognition across accents
- Additional chess-specific voice commands
- More advanced command disambiguation
- Improved automatic calibration
- Better accessibility configuration options
- Expanded teaching and beginner-support features
- Additional operating-system support
- Multiple-language voice recognition
- Improved error handling and user feedback
- Further usability testing with target users

---

## 🧪 Development Status

Say2Check is currently an **academic research prototype** developed as part of a Software Engineering Final Year Project.

The repository contains the main application alongside experimental, training, testing and earlier development modules used throughout the project.

As the project continues to be refined, the repository structure and implementation may change.

---

## 🤝 Project Motivation

Online chess has become increasingly accessible through web and desktop platforms, but conventional interfaces still largely assume that users can accurately operate a mouse, keyboard or touchscreen.

For players with motor impairments, these assumptions can create unnecessary barriers.

Say2Check explores whether technologies such as **speech recognition, computer vision and accessibility overlays** can provide another way to interact with the same chess platforms.

Rather than replacing existing chess websites, the project attempts to create an **assistive layer between the user and the existing interface**.

At the same time, the project's board-recognition and voice-feedback capabilities demonstrate potential beyond accessibility, particularly as an interactive teaching aid for coaches and beginners learning chessboard coordinates and piece positions.

---

## 📚 Academic Project

**Project:** Say2Check – Multi-modal Chess Overlay  
**Project Type:** Final Year Software Engineering Project  
**Institution:** Informatics Institute of Technology (IIT), Sri Lanka  
**Affiliated University:** University of Westminster

The project was developed for academic and research purposes with a focus on accessibility, multimodal human-computer interaction, speech recognition and computer vision.

---

## 📄 License

This repository currently contains academic project work.

A formal open-source license has not yet been assigned.

Until a license is added, the source code remains subject to the repository owner's copyright.

---

## 👤 Author

**A.R. Senevirathna**

Software Engineering Undergraduate  
Informatics Institute of Technology  
University of Westminster

GitHub: **RasinduSen**

---

## ⭐ About the Project

Say2Check demonstrates how **voice recognition, computer vision and desktop interaction** can be combined to explore more accessible ways of interacting with online chess.

The central goal is simple:

> **Make online chess interaction more accessible without taking the game away from the player.**