## file_paths
- src/main/java/traffic/SimulationEngine.java
- src/main/java/traffic/SimulationConfig.java
- src/main/java/traffic/SpawnStrategy.java
- src/main/java/traffic/SimulationCommand.java

## purpose
The files collectively implement a traffic simulation system, with `SimulationEngine` managing the simulation logic, `SimulationConfig` providing default configuration values, `SpawnStrategy` defining vehicle spawning strategies, and `SimulationCommand` allowing command-based interactions with the simulation.

## exports
- `SimulationEngine` (class)
- `SimulationConfig` (class)
- `SpawnStrategy` (interface)
- `SimulationCommand` (interface)

## dependencies
- `java.awt.Color`
- `java.awt.geom.Point2D`
- `java.util.*`
- `java.util.concurrent.CopyOnWriteArrayList`

## architecture_signals
- **Simulation Management**: `SimulationEngine` handles the core logic of the traffic simulation, including vehicle movement, intersection control, and observer notifications.
- **Configuration Management**: `SimulationConfig` provides a singleton pattern for accessing default simulation parameters.
- **Strategy Pattern**: `SpawnStrategy` uses a strategy pattern to determine vehicle spawning logic.
- **Command Pattern**: `SimulationCommand` uses a command pattern to allow external control over simulation parameters.
- **Observer Pattern**: `SimulationEngine` uses an observer pattern to notify `SimulationObserver` instances of simulation updates.

## confidence
0.9