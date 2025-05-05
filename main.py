from core import referral, scheduler, telemetry

if __name__ == "__main__":
    print("TGE-MVP запущен...")
    referral.init_referral_system()
    scheduler.start_post_scheduler()
    telemetry.log_startup()
