# Ticket demo on Render

This branch prepares a single-service live demo of the React frontend and Laravel API. The app serves both from one HTTPS origin. SQLite and the generated Laravel key are stored on the persistent disk at `/data`.

## Render setup

1. Sign in to Render with GitHub and choose **New → Blueprint**.
2. Select `jihoonlabs/jihoon-projects` and branch `deploy/render-demo`.
3. Review the plan before confirming. The Blueprint creates one Starter web service in Singapore and a 1 GB persistent disk.
4. Confirm only if the displayed monthly estimate is acceptable. The Starter service is currently $7/month; the 1 GB disk adds about $0.25/month. The Hobby workspace includes 5 GB of monthly outbound transfer, then additional transfer is billed. This is not a hard cap on total spending.
5. Wait for the first Docker build and deploy to finish. Open the service's `onrender.com` URL and check that the sign-in page loads.
6. Use the demo account details shown in the app's existing demo documentation. Do not enter real candidate or company data.

## Important behavior

- The persistent disk keeps the SQLite database and Laravel key through restarts and deploys.
- Demo seed data is inserted once on first boot. The demo database is separate from local development data.
- Render deploys changes pushed to this branch automatically.
- Stop or delete the service from its Render dashboard when the demo is no longer needed. Deleting the service also removes its persistent disk and demo data.
- This branch is prepared for deployment, but the real Docker image and public service still need a successful build and live browser check in Render.
