import argparse
import json
import sys
import os
import time
import signal

from src.db import init_db, enqueue_job, list_jobs, get_job, list_workers, rem_worker
from src.worker_manager import start
from src.config import set_value
from src.util import now



def cmd_enqueue(a):
    init_db()
    try:
        j=json.loads(a.job_json)
        if not j.get("id") or not j.get("command"):
            print("Job must contain id and command");return
        enqueue_job(j["id"],j["command"],now())
        print(f"Enqueued {j['id']}")
    except Exception as e:
        print("Invalid JSON:",e)

def cmd_worker_start(a):
    init_db()
    print(f"Starting {a.count} worker(s)... Ctrl+C to stop")
    try:start(a.count)
    except KeyboardInterrupt:print("Stopped workers")

def cmd_status(a):
    init_db()
    s=["pending","processing","completed","failed","dead"]
    for st in s:
        print(st,":",len(list_jobs(st)))
    print("Workers:",len(list_workers()))

def cmd_list(a):
    init_db()
    r=list_jobs(a.state)
    for x in r:print(json.dumps({"id":x[0],"cmd":x[1],"state":x[2],"att":x[3],"err":x[4]}))

def cmd_dlq_list(a):
    init_db()
    for x in list_jobs("dead"):print(json.dumps({"id":x[0],"cmd":x[1],"err":x[4]}))

def cmd_dlq_retry(a):
    from db import enqueue_job
    j=get_job(a.job_id)
    if not j:print("Job not found");return
    enqueue_job(j[0],j[1],now())
    print("Retried",j[0])

def cmd_cfg_set(a):
    init_db()
    set_value(a.key,a.value)
    print("OK")

def build():
    p=argparse.ArgumentParser(prog="queuectl")
    sub=p.add_subparsers(dest="cmd")

    en=sub.add_parser("enqueue");en.add_argument("job_json");en.set_defaults(f=cmd_enqueue)
    wk=sub.add_parser("worker");wk.add_argument("action",choices=["start"]);wk.add_argument("--count",type=int,default=1);wk.set_defaults(f=cmd_worker_start)
    st=sub.add_parser("status");st.set_defaults(f=cmd_status)
    ls=sub.add_parser("list");ls.add_argument("--state");ls.set_defaults(f=cmd_list)
    dq=sub.add_parser("dlq");dqsub=dq.add_subparsers(dest="dqcmd")
    dql=dqsub.add_parser("list");dql.set_defaults(f=cmd_dlq_list)
    dqr=dqsub.add_parser("retry");dqr.add_argument("job_id");dqr.set_defaults(f=cmd_dlq_retry)
    cfg=sub.add_parser("config");cfgsub=cfg.add_subparsers(dest="ccmd")
    sc=cfgsub.add_parser("set");sc.add_argument("key");sc.add_argument("value");sc.set_defaults(f=cmd_cfg_set)
    return p

def main(argv=None):
    p=build();a=p.parse_args(argv)
    if not hasattr(a,"f"):p.print_help();return
    a.f(a)

if __name__=="__main__":
    main()
