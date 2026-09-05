# Architecture

## Core
The system is built around a small, stable core and independent modules.

```text
Haji Business
├── Core
│   ├── Memory
│   ├── Commands
│   ├── Tasks
│   ├── Permissions
│   └── Notifications
└── Modules
    ├── Prayer
    ├── Sports
    ├── Business
    ├── Al-Mashareq Al-Oula
    ├── Trading
    └── Communication
```

## Execution flow
1. Receive user command.
2. Resolve intent and required task.
3. Load relevant memory/context.
4. Check permissions and risk level.
5. Execute safe actions automatically.
6. Ask for explicit approval before financial or sensitive commitments.
7. Record the result and notify the user.

## Modular rule
Each module must be independently replaceable and communicate with the core through stable interfaces. Business logic should not be hard-coded into the core.
