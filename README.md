# RoyalWheels Render Deployment

This project is a Django app in `backend/` and is now set up for Render.

## What was added

- Production database support through `DATABASE_URL`
- Static file serving through WhiteNoise
- Gunicorn for the Render web service
- A `render.yaml` blueprint for one-click setup

## Render setup

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and select this repository.
3. Render will create:
   - one `web` service for Django
   - one PostgreSQL database
4. Set the missing environment variables in Render:
   - `DJANGO_SECRET_KEY`
   - `GOOGLE_CLIENT_ID`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
   - `DEFAULT_FROM_EMAIL`
   - `FAST2SMS_API_KEY` if you use it
5. Deploy.

## Manual Render commands

- Build command: `cd backend && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start command: `cd backend && gunicorn backend.wsgi:application`

## Notes

- Do not use SQLite on Render. Attach the provided PostgreSQL database.
- `backend/.env.example` now contains placeholders only. Put real secrets in Render environment variables, not in git.
- Uploaded media files in `backend/media/` are not persistent on Render's web service filesystem. If you need permanent uploads, move media storage to a service like Cloudinary, S3, or Render disk-backed storage on a paid plan.
