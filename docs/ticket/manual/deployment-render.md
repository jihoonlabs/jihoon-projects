# Ticket demo on Render

This branch is based on the current `main` branch and prepares the public Ticket demo for Render. The React frontend and Laravel API run in one Docker web service, served from a single HTTPS origin. SQLite data and the generated Laravel key are stored on a persistent disk at `/data`.

## Create the service

1. Sign in to Render with GitHub and choose **New → Blueprint**.
2. Select `jihoonlabs/jihoon-projects` and branch `deploy/render-demo-main`.
3. Review the Blueprint. It creates one Starter web service in Singapore and a 1 GB persistent disk.
4. Check the current estimate and included usage before confirming. The Starter web service is currently $7/month and the 1 GB disk adds about $0.25/month. Additional outbound transfer beyond the workspace allowance is billed, so this is not a hard cap on total spending.
5. Wait for the Docker build and deploy to finish. Open the generated `onrender.com` URL, sign in with the demo account shown on the login screen, and try the Ticket board.
6. Use only the fictional demo data. Do not enter real candidate or company information.

## Notes

- The persistent disk keeps the SQLite database and Laravel key through restarts and deploys.
- Demo seed data is inserted once when the disk has no seed marker.
- Render deploys future commits to this branch automatically.
- Stop or delete the service from Render when the demo is no longer needed. Deleting the service also deletes the disk and demo data.
- The deployment is not live until the real Docker build succeeds and the public site is checked in a browser.
