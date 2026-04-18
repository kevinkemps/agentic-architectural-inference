## file_paths
- src/main/java/traffic/SimulationEngine.java
- src/main/java/traffic/SimulationConfig.java
- src/main/java/traffic/SpawnStrategy.java
- src/main/java/traffic/SimulationCommand.java

## purpose
The purpose of these files is to implement a traffic simulation system, including the core simulation engine, configuration settings, vehicle spawn strategy, and command pattern for UI interactions.

## exports
- `SimulationEngine`
- `SimulationConfig`
- `SpawnStrategy`
- `SimulationCommand`

## dependencies
- `java.awt.Color`
- `java.awt.geom.Point2D`
- `java.util.ArrayDeque`
- `java.util.ArrayList`
- `java.util.Deque`
- `java.util.List`
- `java.util.Map`
- `java.util.Objects`
- `java.util.Random`
- `java.util.concurrent.CopyOnWriteArrayList`

## architecture_signals
- **Simulation Engine**: The `SimulationEngine` class is the core component that manages the traffic simulation, including vehicle movement, intersection control, and observer notifications.
- **Configuration Management**: The `SimulationConfig` class provides a singleton pattern for managing default simulation settings.
- **Strategy Pattern**: The `SpawnStrategy` interface defines a strategy pattern for determining where new vehicles should spawn.
- **Command Pattern**: The `SimulationCommand` interface implements the command pattern to allow UI-driven changes to the simulation state.

## confidence
0.9