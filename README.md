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
   - `RESEND_API_KEY` for production OTP email delivery
   - `RESEND_FROM_EMAIL` using a verified sender/domain in Resend
   - `DEFAULT_FROM_EMAIL`
   - `FAST2SMS_API_KEY` if you use it
   - `CLOUDINARY_URL` for persistent admin-uploaded vehicle images
5. Deploy.

## Manual Render commands

- Build command: `cd backend && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start command: `cd backend && gunicorn backend.wsgi:application`

## Notes

- Do not use SQLite on Render. Attach the provided PostgreSQL database.
- `backend/.env.example` now contains placeholders only. Put real secrets in Render environment variables, not in git.
- OTP email delivery is now designed to use Resend first. SMTP settings remain as a fallback for local or legacy setups.
- Admin-uploaded vehicle images are now designed to use Cloudinary when `CLOUDINARY_URL` or the Cloudinary credential variables are set.
- Existing vehicle records that currently point to missing local files need one re-upload in the admin panel so their `photo_url` is updated to the Cloudinary URL.
- Other uploaded files still use local media unless you extend Cloudinary usage to those fields too.
