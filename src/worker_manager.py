import multiprocessing, subprocess, time, signal, os
from src.db import fetch_next_job, mark_completed, mark_failed, move_dead, add_worker, rem_worker
from src.config import backoff_base, max_retries

_stop = multiprocessing.Event()

def _run(cmd):
    try:
        p = subprocess.run(cmd, shell=True)
        return p.returncode
    except Exception:
        return 1

def loop(worker_id):
    pid = os.getpid()
    add_worker(pid, int(time.time()))
    signal.signal(signal.SIGINT, lambda s, f: _stop.set())
    signal.signal(signal.SIGTERM, lambda s, f: _stop.set())

    while not _stop.is_set():
        now = int(time.time())
        job = fetch_next_job(now)
        if not job:
            time.sleep(1)
            continue

        rc = _run(job["command"])
        now2 = int(time.time())

        # ---------------- FIXED SECTION ----------------
        attempts = job["attempts"] + 1
        if rc == 0:
            mark_completed(job["id"], now2)
        elif attempts >= max_retries():
            move_dead(job["id"], f"exit {rc}", now2)
        else:
            delay = backoff_base() ** attempts
            mark_failed(job["id"], f"exit {rc}", attempts, now2 + delay, now2)
        # ------------------------------------------------

    rem_worker(pid)

def start(n):
    ps = []
    for i in range(n):
        p = multiprocessing.Process(target=loop, args=(i,))
        p.start()
        ps.append(p)
    for p in ps:
        p.join()
