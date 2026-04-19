## file_paths
- README.md

## purpose
The README.md file provides an overview of the Traffic Simulator application, including its requirements, how to run it, and the design patterns used in its implementation.

## exports
none

## dependencies
none

## architecture_signals
- Documentation: Provides an overview of the application's purpose and usage.
- Design Patterns: Lists the design patterns used in the application, such as Factory, Builder, Strategy, Observer, Command, State, Template Method, and Singleton.

## confidence
0.9

---

## file_paths
- build/reports/tests/test/js/report.js

## purpose
This JavaScript file is part of the test report generation, handling the UI interactions for viewing test results.

## exports
none

## dependencies
none

## architecture_signals
- Test Reporting: Manages the display and interaction of test results in a web-based report.

## confidence
0.8

---

## file_paths
- src/test/java/traffic/SimulationEngineTest.java

## purpose
This file contains unit tests for the SimulationEngine class, verifying its behavior and interactions with other components.

## exports
- SimulationEngineTest

## dependencies
- org.junit.jupiter.api.Test
- SimulationConfig
- SimulationEngine
- SimulationEngineBuilder
- VehicleFactory
- PaletteColorStrategy
- FixedSpawnStrategy
- SimulationObserver

## architecture_signals
- Testing: Provides unit tests for the SimulationEngine, ensuring correct functionality and integration with other components.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/BiasedSpawnStrategy.java

## purpose
Implements a weighted random strategy for spawning vehicles, preferring the main road over others.

## exports
- BiasedSpawnStrategy

## dependencies
- SpawnStrategy
- SimulationEngine.Road

## architecture_signals
- Strategy Pattern: Implements a strategy for vehicle spawning with weighted preferences.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/TrafficPanel.java

## purpose
The TrafficPanel class is responsible for rendering the traffic simulation, including roads, vehicles, and traffic signals.

## exports
- TrafficPanel

## dependencies
- javax.swing.JPanel
- SimulationEngine
- SimulationSnapshot
- SimulationCommands

## architecture_signals
- UI Rendering: Handles the graphical representation of the simulation, including user interactions with traffic signals.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/VehicleFactory.java

## purpose
The VehicleFactory class is responsible for creating vehicle instances with specific color strategies.

## exports
- VehicleFactory

## dependencies
- ColorStrategy
- SimulationEngine.Vehicle
- SimulationEngine.Road

## architecture_signals
- Factory Pattern: Creates vehicle instances with configurable color strategies.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/SimulationSnapshot.java

## purpose
Provides an immutable view of the simulation state for observers and UI components.

## exports
- SimulationSnapshot

## dependencies
- SimulationEngine.RoadView
- SimulationEngine.VehicleView
- SimulationEngine.SignalView

## architecture_signals
- Observer Pattern: Facilitates the distribution of simulation state to observers.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/SimulationCommands.java

## purpose
Defines common simulation commands used by the UI to interact with the simulation engine.

## exports
- SimulationCommands

## dependencies
- SimulationCommand
- SimulationEngine

## architecture_signals
- Command Pattern: Encapsulates actions as command objects for UI interaction.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/SimulationEngineBuilder.java

## purpose
The SimulationEngineBuilder class provides a flexible way to construct SimulationEngine instances with various configurations.

## exports
- SimulationEngineBuilder

## dependencies
- SimulationEngine
- SimulationConfig
- BiasedSpawnStrategy
- PaletteColorStrategy
- VehicleFactory

## architecture_signals
- Builder Pattern: Facilitates flexible and testable construction of SimulationEngine instances.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/SimulationObserver.java

## purpose
Defines an interface for observers that are notified after each simulation tick.

## exports
- SimulationObserver

## dependencies
- SimulationSnapshot

## architecture_signals
- Observer Pattern: Allows components to be notified of simulation updates.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/TrafficSimulatorApp.java

## purpose
The TrafficSimulatorApp class is the main application entry point, setting up the UI and starting the simulation loop.

## exports
- TrafficSimulatorApp

## dependencies
- javax.swing
- SimulationEngine
- SimulationEngineBuilder
- TrafficPanel
- SimulationCommands

## architecture_signals
- Application Entry Point: Initializes and runs the traffic simulation application.
- UI Management: Sets up and manages the user interface components.

## confidence
0.9

## entrypoints
- cli command: main method in TrafficSimulatorApp

---

## file_paths
- src/main/java/traffic/PaletteColorStrategy.java

## purpose
Implements a color strategy that selects vehicle colors from a predefined palette.

## exports
- PaletteColorStrategy

## dependencies
- ColorStrategy

## architecture_signals
- Strategy Pattern: Provides a specific strategy for selecting vehicle colors.

## confidence
0.9

---

## file_paths
- src/main/java/traffic/ColorStrategy.java

## purpose
Defines an interface for strategies that determine vehicle colors.

## exports
- ColorStrategy

## dependencies
none

## architecture_signals
- Strategy Pattern: Defines a contract for color selection strategies.

## confidence
0.9