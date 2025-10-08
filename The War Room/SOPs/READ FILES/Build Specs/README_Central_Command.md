# Central Command – Reporting & Evidence Engine

Central Command is a modular operations and evidence system engineered for investigative and intelligence workflows.  
It integrates orchestration, validation, secure evidence handling, and automated reporting.

---

## Features
- ECC drift guard and validation engine (The Warden).  
- Secure gateway and evidence routing (The Marshall).  
- Evidence Locker with manifest, classifier, index, archive.  
- Analyst Deck with modular report assembly pipelines.  
- War Room for isolated processors and agent configs.  
- Ops Center for automation and stress diagnostics.  
- Command Center providing orchestration, UI, plugins.  

---

## Quickstart
```bash
make setup                     # Initialize environment + sync War Room processors
make run                       # Launch Command Center
make spawn-agent NAME=AgentX    # Provision new agent environment
make archive-case ID=Case001    # Archive evidence package
make diagnostics               # Execute system stress tests
```

---

## Directory Structure
- **Command Center/** → Orchestration, UI, Plugins.  
- **The Warden/** → ECC, Validation controllers.  
- **The Marshall/** → Gateway, Evidence Manager.  
- **Evidence Locker/** → Case builders, archives.  
- **The Analyst Deck/** → Scaffolding, renderers, test plans.  
- **The War Room/** → Processors, SOPs, Agent envs.  
- **Ops Center/** → Automation scripts, Library, Stress Tests.  
