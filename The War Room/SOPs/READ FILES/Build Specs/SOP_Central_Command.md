# Standard Operating Procedure (SOP) – Central Command

## 1. Objective
Define operational workflows for system administrators, developers, and investigative operators to ensure consistency and compliance in the operation of Central Command.

## 2. System Startup
1. Execute `make setup` – Initializes Python environment and synchronizes War Room processors.
2. Execute `make run` – Boots Command Center orchestration layer.
3. Validate ECC startup logs indicate: `[Warden: ONLINE]`.

## 3. Evidence Lifecycle
- **Ingress:** All evidence enters through The Marshall (Gateway).  
- **Validation:** The Warden executes ECC validation cycles.  
- **Storage:** Evidence is sealed in the Evidence Locker with manifest and index.  
- **Archival:** `make archive-case ID=<CaseRef>` generates immutable archive bundles.  

## 4. Agent Lifecycle
- **Provisioning:** `make spawn-agent NAME=<AgentID>` auto-creates:  
  - `/War Room/dev_tracking/<AgentID>/directions.yaml`  
  - `/War Room/dev_tracking/<AgentID>/env.json`  
  - `/War Room/dev_tracking/<AgentID>/last_run.log`  
- **Execution:** Agent environments reference War Room Processors.  

## 5. Diagnostics & Recovery
- **Diagnostics:** `make diagnostics` executes Ops Center Stress Tests.  
- **Recovery:** `make clean` clears transient caches/logs; sealed archives provide case restoration.  
