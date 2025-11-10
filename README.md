# QueueCTL – Background Job Queue System (CLI)

Author: Ramineni Vamsidhar  
Company: Flam  
Language: Python 3  
Platform: Windows 10  
Submission: Flam – Backend Developer Internship Assignment  

---

## Objective
`queuectl` is a CLI-based background job queue system that manages asynchronous jobs with:
- Multi-process workers  
- Automatic retries using exponential backoff  
- Persistent SQLite storage  
- Dead Letter Queue (DLQ) for permanently failed jobs  
- Configurable runtime parameters through CLI  

---

## Tech Stack
- Python 3.13  
- SQLite3 (persistent storage)  
- Multiprocessing (parallel workers)  
- Subprocess (job execution)  
- Argparse (CLI parsing)

---

## Architecture Overview

### Job Lifecycle
pending → processing → completed / failed → dead (DLQ)

### Modules
| Module | Responsibility |
|---------|----------------|
| `queuectl.py` | CLI entry-point (enqueue, worker, dlq, config, etc.) |
| `worker_manager.py` | Worker pool, retry logic, exponential backoff |
| `db.py` | SQLite persistence for jobs, config, and workers |
| `config.py` | Load/store runtime configuration |
| `util.py` | Helper functions (timestamps, formatting) |

### Retry Algorithm
delay = (backoff_base) ^ (attempts)
Default: base = 2, max_retries = 3

### Dead Letter Queue
When a job’s `attempts >= max_retries`, it is moved to the DLQ table.  
DLQ jobs can be inspected or re-queued manually.

### Data Storage
- File: `~/.queuectl.sqlite3`
- Persists all jobs, workers, and configuration across restarts.

---

## Setup Instructions

1. Clone the repository
   ```bash
   git clone https://github.com/<your-username>/queuectl-python.git
   cd queuectl-python
Verify Python launcher

& "C:\Users\<you>\AppData\Local\Programs\Python\Launcher\py.exe" --version

Dependencies
Uses only Python’s standard library
Initialize database
python -m src.queuectl status
Usage Examples
Enqueue a Job
py -m src.queuectl enqueue "{\"id\":\"job1\",\"command\":\"echo Hello Flam\"}"
Start Worker(s)
py -m src.queuectl worker start --count 2
# Ctrl + C to stop gracefully
Check Status
py -m src.queuectl status

List Jobs by State
py -m src.queuectl list --state completed
View or Retry DLQ
py -m src.queuectl dlq list
py -m src.queuectl dlq retry job_fail_test
Configure Runtime Values
py -m src.queuectl config set max_retries 3
py -m src.queuectl config set backoff_base 2


Testing Instructions
Basic Flow

Start a worker

py -m src.queuectl worker start --count 1


Enqueue success job

py -m src.queuectl enqueue "{\"id\":\"job_ok\",\"command\":\"echo Hello Flam\"}"


Enqueue fail job

py -m src.queuectl config set max_retries 1
py -m src.queuectl enqueue "{\"id\":\"job_fail_test\",\"command\":\"false\"}"


Observe

status shows dead : 1

dlq list shows {"id":"job_fail_test","cmd":"false","err":"exit 1"}

Retry from DLQ

py -m src.queuectl dlq retry job_fail_test

DEMO
[ https://drive.google.com/your-demo-link](https://drive.google.com/file/d/1PDspkk6B1prxCNiXzg7p94MPGcuebka4/view?usp=drive_link)

Conclusion

QueueCTL delivers a minimal, production-ready job queue system with persistence, retries, DLQ handling, and a clean CLI.
All core requirements for the Flam Backend Developer Internship have been verified successfully on Windows 10 with Python 3.13.



