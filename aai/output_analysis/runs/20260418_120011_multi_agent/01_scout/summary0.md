## file_paths
- README.md

## purpose
The README file provides an overview of the Traffic Simulator application, including its requirements, how to run it, and the design patterns used in its implementation.

## exports
none

## dependencies
none

## architecture_signals
- Documentation: Provides an overview of the application's purpose and usage.
- Design Patterns: Lists the design patterns used in the application, such as Factory, Builder, Strategy, Observer, Command, State, Template Method, and Singleton.

## confidence
0.9

## file_paths
- build/reports/tests/test/js/report.js

## purpose
This JavaScript file is part of the test report generation, handling the UI for displaying test results in a tabbed format.

## exports
none

## dependencies
none

## architecture_signals
- Test Reporting: Manages the UI for displaying test results.

## confidence
0.8

## file_paths
- src/test/java/traffic/SimulationEngineTest.java

## purpose
This file contains unit tests for the `SimulationEngine` class, verifying its behavior and ensuring it functions correctly.

## exports
- SimulationEngineTest

## dependencies
- org.junit.jupiter.api.Test
- java.awt.geom.Point2D
- java.util.Random
- java.util.concurrent.atomic.AtomicInteger
- traffic.SimulationConfig
- traffic.SimulationEngine
- traffic.SimulationEngineBuilder
- traffic.VehicleFactory
- traffic.SpawnStrategy
- traffic.SimulationObserver

## architecture_signals
- Testing: Contains unit tests for the `SimulationEngine` class.

## confidence
0.9

## file_paths
- src/main/java/traffic/BiasedSpawnStrategy.java

## purpose
Implements a weighted random strategy for spawning vehicles, preferring the main road over others.

## exports
- BiasedSpawnStrategy

## dependencies
- java.util.List
- java.util.Map
- java.util.Random
- traffic.SpawnStrategy
- traffic.SimulationEngine.Road

## architecture_signals
- Strategy Pattern: Implements a strategy for vehicle spawning.

## confidence
0.9

## file_paths
- src/main/java/traffic/TrafficPanel.java

## purpose
The `TrafficPanel` class is responsible for rendering the traffic simulation on a JPanel, including roads, vehicles, and traffic signals.

## exports
- TrafficPanel

## dependencies
- javax.swing.JPanel
- java.awt.*
- java.awt.event.MouseAdapter
- java.awt.event.MouseEvent
- traffic.SimulationEngine
- traffic.SimulationSnapshot
- traffic.SimulationCommands

## architecture_signals
- UI Rendering: Handles the graphical representation of the traffic simulation.

## confidence
0.9

## file_paths
- src/main/java/traffic/VehicleFactory.java

## purpose
The `VehicleFactory` class is responsible for creating vehicle instances with specific color strategies.

## exports
- VehicleFactory

## dependencies
- java.awt.Color
- java.util.Objects
- java.util.Random
- traffic.ColorStrategy
- traffic.SimulationEngine.Vehicle
- traffic.SimulationEngine.Road

## architecture_signals
- Factory Pattern: Creates vehicle instances with specific attributes.

## confidence
0.9

## file_paths
- src/main/java/traffic/SimulationSnapshot.java

## purpose
The `SimulationSnapshot` class provides an immutable view of the simulation state for observers and the UI.

## exports
- SimulationSnapshot

## dependencies
- java.awt.Graphics2D
- java.util.List
- traffic.SimulationEngine.RoadView
- traffic.SimulationEngine.VehicleView
- traffic.SimulationEngine.SignalView

## architecture_signals
- Observer Pattern: Provides a snapshot of the simulation state for observers.

## confidence
0.9

## file_paths
- src/main/java/traffic/SimulationCommands.java

## purpose
Defines common simulation commands used by the UI to interact with the simulation engine.

## exports
- SimulationCommands

## dependencies
- traffic.SimulationCommand
- traffic.SimulationEngine

## architecture_signals
- Command Pattern: Encapsulates actions as command objects.

## confidence
0.9

## file_paths
- src/main/java/traffic/SimulationEngineBuilder.java

## purpose
The `SimulationEngineBuilder` class provides a flexible and testable way to construct `SimulationEngine` instances.

## exports
- SimulationEngineBuilder

## dependencies
- java.awt.geom.Point2D
- java.util.Objects
- java.util.Random
- traffic.SimulationEngine
- traffic.SpawnStrategy
- traffic.ColorStrategy
- traffic.VehicleFactory
- traffic.SimulationConfig

## architecture_signals
- Builder Pattern: Constructs `SimulationEngine` instances with customizable parameters.

## confidence
0.9

## file_paths
- src/main/java/traffic/SimulationObserver.java

## purpose
The `SimulationObserver` interface defines a contract for objects that need to be notified after each simulation tick.

## exports
- SimulationObserver

## dependencies
- traffic.SimulationSnapshot

## architecture_signals
- Observer Pattern: Defines an interface for receiving updates from the simulation.

## confidence
0.9

## file_paths
- src/main/java/traffic/TrafficSimulatorApp.java

## purpose
The `TrafficSimulatorApp` class is the main application class for the traffic simulator, setting up the UI and starting the simulation loop.

## exports
- TrafficSimulatorApp

## dependencies
- javax.swing.*
- java.awt.*
- java.awt.event.ActionEvent
- java.awt.event.ActionListener
- traffic.SimulationEngine
- traffic.SimulationEngineBuilder
- traffic.TrafficPanel
- traffic.SimulationCommands

## architecture_signals
- Application Entry Point: Initializes and runs the traffic simulation application.
- UI Management: Sets up and manages the user interface components.

## confidence
0.9

## file_paths
- src/main/java/traffic/PaletteColorStrategy.java

## purpose
The `PaletteColorStrategy` class provides a strategy for selecting vehicle colors from a predefined palette.

## exports
- PaletteColorStrategy

## dependencies
- java.awt.Color
- java.util.Random
- traffic.ColorStrategy

## architecture_signals
- Strategy Pattern: Implements a color selection strategy for vehicles.

## confidence
0.9

## file_paths
- src/main/java/traffic/ColorStrategy.java

## purpose
The `ColorStrategy` interface defines a strategy for picking vehicle colors.

## exports
- ColorStrategy

## dependencies
- java.awt.Color
- java.util.Random

## architecture_signals
- Strategy Pattern: Defines an interface for color selection strategies.

## confidence
0.9