from apscheduler.schedulers.background import BackgroundScheduler

_scheduler: BackgroundScheduler | None = None

def init_scheduler():
    global _scheduler
    if _scheduler:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.start()

def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
