#!/bin/bash

# Script to initialize SSL certificates for concord-saia.bineyes.com

DOMAIN="concord-saia.bineyes.com"
EMAIL="admin@bineyes.com"  # تغيير إلى بريدك الإلكتروني

# Create directories for certbot
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Start nginx temporarily with HTTP only for certificate validation
echo "Starting nginx temporarily for certificate generation..."
docker-compose up -d nginx

# Wait for nginx to start
sleep 5

# Get SSL certificate
echo "Obtaining SSL certificate from Let's Encrypt..."
docker-compose run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Restart nginx with HTTPS configuration
echo "Restarting nginx with HTTPS enabled..."
docker-compose restart nginx

echo "SSL certificate setup complete!"
echo "Your site should now be accessible at https://$DOMAIN"
