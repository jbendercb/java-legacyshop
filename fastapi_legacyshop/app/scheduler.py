from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import logging

from app.database import SessionLocal
from app.services.inventory_service import InventoryService
from app.services.loyalty_service import LoyaltyService

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


async def scheduled_inventory_replenishment():
    logger.info("Starting scheduled inventory replenishment")
    db = SessionLocal()
    try:
        service = InventoryService(db)
        await service.replenish_inventory()
        logger.info("Completed scheduled inventory replenishment")
    except Exception as e:
        logger.error(f"Error in scheduled inventory replenishment: {str(e)}")
    finally:
        db.close()


async def scheduled_loyalty_processing():
    logger.info("Starting scheduled loyalty points processing")
    db = SessionLocal()
    try:
        service = LoyaltyService(db)
        await service.process_loyalty_points()
        logger.info("Completed scheduled loyalty points processing")
    except Exception as e:
        logger.error(f"Error in scheduled loyalty processing: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        func=scheduled_inventory_replenishment,
        trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
        id='inventory_replenishment',
        name='Nightly Inventory Replenishment',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=scheduled_loyalty_processing,
        trigger=IntervalTrigger(minutes=30),  # Every 30 minutes
        id='loyalty_processing',
        name='Loyalty Points Processing',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started with inventory replenishment and loyalty processing jobs")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
