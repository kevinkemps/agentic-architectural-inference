## file_paths
- src/main/java/traffic/SimulationEngine.java
- src/main/java/traffic/SimulationConfig.java
- src/main/java/traffic/SpawnStrategy.java
- src/main/java/traffic/SimulationCommand.java

## purpose
The files collectively implement a traffic simulation system, with `SimulationEngine` managing the simulation logic, `SimulationConfig` providing default configuration values, `SpawnStrategy` defining vehicle spawning strategies, and `SimulationCommand` allowing command-based interactions with the simulation.

## exports
- `SimulationEngine`
- `SimulationConfig`
- `SpawnStrategy`
- `SimulationCommand`

## dependencies
- `java.awt.Color`
- `java.awt.geom.Point2D`
- `java.util.*`
- `java.util.concurrent.CopyOnWriteArrayList`

## architecture_signals
- **Simulation Management**: `SimulationEngine` handles the core simulation logic, including vehicle movement, intersection control, and observer notifications.
- **Configuration Management**: `SimulationConfig` provides a singleton pattern for accessing default simulation parameters.
- **Strategy Pattern**: `SpawnStrategy` uses an interface to define different strategies for vehicle spawning.
- **Command Pattern**: `SimulationCommand` allows external commands to modify the simulation state.

## confidence
0.9