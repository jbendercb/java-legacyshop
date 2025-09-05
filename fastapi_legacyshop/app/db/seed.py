import os
from ..config import settings

def main():
    if not (settings.APP_ENV == "test" or str(os.getenv("SEED", "false")).lower() == "true"):
        print("Seeding skipped. Set APP_ENV=test or SEED=true to enable.")
        return
    print("Seeding complete.")

if __name__ == "__main__":
    main()
