"""Server entry point for OpenEnv validator compatibility."""
import uvicorn
from clinical_trial_auditor.server.app import app

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
